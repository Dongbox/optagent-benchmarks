from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from optagent import ModelBuilder

from benchmarks.cases.base import BenchmarkCase

SOURCE = "JSPLIB via ScheduleOpt"
SOURCE_KEY = "jsplib"
PROBLEM_TYPE = "scheduling"
INSTANCE_TYPE = "jobshop"
FAMILY = "interval_job_shop"
MODEL_STYLE = "interval_var_sequence_no_overlap_precedence"
RAW_DIR = Path(__file__).resolve().parent / "raw"


@dataclass(frozen=True)
class JobShopOperation:
    job: int
    operation: int
    machine: int
    duration: int


@dataclass(frozen=True)
class JobShopInstance:
    name: str
    jobs: int
    machines: int
    operations: tuple[JobShopOperation, ...]
    family: str | None = None
    family_long: str | None = None
    year: str | None = None

    @property
    def operation_count(self) -> int:
        return len(self.operations)

    @property
    def horizon(self) -> int:
        return sum(operation.duration for operation in self.operations)

    def operations_by_job(self) -> dict[int, tuple[JobShopOperation, ...]]:
        grouped: dict[int, list[JobShopOperation]] = {job: [] for job in range(self.jobs)}
        for operation in self.operations:
            grouped.setdefault(operation.job, []).append(operation)
        return {
            job: tuple(sorted(items, key=lambda item: item.operation))
            for job, items in sorted(grouped.items())
        }

    def operations_by_machine(self) -> dict[int, tuple[JobShopOperation, ...]]:
        grouped: dict[int, list[JobShopOperation]] = {machine: [] for machine in range(self.machines)}
        for operation in self.operations:
            grouped.setdefault(operation.machine, []).append(operation)
        return {
            machine: tuple(sorted(items, key=lambda item: (item.job, item.operation)))
            for machine, items in sorted(grouped.items())
        }


class JobShopCase(BenchmarkCase):
    def build_model(self, **kwargs: Any) -> ModelBuilder:
        allow_download = bool(kwargs.get("allow_download", True))
        instance = load_job_shop_case(self.to_row(), cache_dir=RAW_DIR, allow_download=allow_download)
        horizon = max(0, instance.horizon)
        builder = ModelBuilder(metadata={"model_style": MODEL_STYLE})

        operation_vars: dict[tuple[int, int], Any] = {}
        operation_node_ids: dict[tuple[int, int], int] = {}
        for operation in instance.operations:
            key = _operation_key(operation)
            interval = builder.interval_var(
                start=0,
                length=operation.duration,
                lb_start=0,
                ub_start=horizon,
                lb_length=operation.duration,
                ub_length=operation.duration,
                name=f"op_j{operation.job}_k{operation.operation}_m{operation.machine}",
            )
            operation_vars[key] = interval
            operation_node_ids[key] = interval.node_id

        machine_sequence_node_ids: dict[int, int] = {}
        machine_operation_keys: dict[int, tuple[tuple[int, int], ...]] = {}
        for machine, operations in instance.operations_by_machine().items():
            keys = tuple(_operation_key(operation) for operation in operations)
            sequence = builder.sequence_var(size=len(keys), default=list(range(len(keys))), name=f"machine_{machine}_order")
            machine_sequence_node_ids[machine] = sequence.node_id
            machine_operation_keys[machine] = keys
            builder.constraint(builder.no_overlap(sequence, *(operation_vars[key] for key in keys)), name=f"machine_{machine}_capacity")

        last_operation_ends = []
        for job, operations in instance.operations_by_job().items():
            if len(operations) != instance.machines:
                raise ValueError(f"job {job} has {len(operations)} operations, expected {instance.machines}")
            for before, after in zip(operations, operations[1:]):
                builder.constraint(
                    builder.precedence(operation_vars[_operation_key(before)], operation_vars[_operation_key(after)], lag=0),
                    name=f"job_{job}_op_{before.operation}_before_{after.operation}",
                )
            last_operation_ends.append(builder.interval_end(operation_vars[_operation_key(operations[-1])]))

        objective = builder.minimize(builder.max(*last_operation_ends), name="makespan")
        self._set_build_context(
            {
                "instance": instance,
                "operation_node_ids": operation_node_ids,
                "machine_sequence_node_ids": machine_sequence_node_ids,
                "machine_operation_keys": machine_operation_keys,
                "objective_node_id": objective.node_id,
                "horizon": horizon,
            }
        )
        return builder

    def solution_metrics(self, solution: Any, **kwargs: Any) -> dict[str, Any]:
        context = self._build_context()
        raw_objective = _solution_objective(context, solution.variable_values, solution.objective_value)
        objective = raw_objective if solution.feasible else None
        instance = context["instance"]
        return {
            "objective": float(objective) if objective is not None else None,
            "raw_objective": float(raw_objective) if raw_objective is not None else None,
            "model_style": MODEL_STYLE,
            "decoded_solution": {
                "kind": "job_shop_schedule",
                "machine_orders": _decoded_machine_orders(context, solution.variable_values),
            },
            "metadata": {
                "jobs": instance.jobs,
                "machines": instance.machines,
                "horizon": context["horizon"],
            },
        }


def make_job_shop_case(
    *,
    benchmark_id: str,
    instance: str,
    tier: str,
    jobs: int,
    machines: int,
    raw_path: str | Path,
    objective: int,
    case_module: str,
    reported_time_seconds: int | None = None,
    instance_url: str | None = None,
    reference: dict[str, Any] | None = None,
) -> JobShopCase:
    compare_key = f"{SOURCE_KEY}/{PROBLEM_TYPE}/{INSTANCE_TYPE}/{instance}"
    effective_reference = {
        "lower_bound": objective,
        "objective": objective,
        "reported_machine": "i7-1185G7 @ 3.00GHz",
        "reported_solver": "OptalCP",
        "source_url": "https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/solutions/bks.json",
        "status": "closed",
        "upper_bound": objective,
        "value_kind": "optimal",
    }
    if reported_time_seconds is not None:
        effective_reference["reported_time_seconds"] = reported_time_seconds
    if reference:
        effective_reference.update(reference)
    data: dict[str, Any] = {
        "raw_path": str(raw_path),
        "documentation_url": "https://scheduleopt.github.io/benchmarks/jsplib/",
        "solution_url": "https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/solutions/bks.json",
    }
    if instance_url is not None:
        data["instance_url"] = instance_url

    return JobShopCase(
        benchmark_id=benchmark_id,
        source=SOURCE,
        problem_type=PROBLEM_TYPE,
        instance_type=INSTANCE_TYPE,
        instance=instance,
        family=FAMILY,
        tier=tier,
        compare_key=compare_key,
        series_key=f"{compare_key}/{MODEL_STYLE}",
        size={"jobs": jobs, "machines": machines, "operations": jobs * machines},
        data=data,
        reference=effective_reference,
        problem_description=(
            f"JSPLIB job-shop instance {instance}: schedule {jobs} jobs across {machines} machines. "
            "Each job has a fixed machine route and fixed operation durations; each machine can "
            "process at most one operation at a time. The benchmark objective is minimum makespan."
        ),
        case_module=case_module,
        modeling_notes={
            "model_style": MODEL_STYLE,
            "objective_sense": "minimize",
            "public_api_primitives": ["interval_var", "sequence_var", "no_overlap", "precedence", "max"],
        },
    )


def parse_scheduleopt_jsplib_json(text: str) -> JobShopInstance:
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("ScheduleOpt JSPLIB JSON root must be an object")

    name = str(payload.get("instance") or "").strip()
    if not name:
        raise ValueError("ScheduleOpt JSPLIB JSON requires an instance name")

    jobs = int(payload.get("jobs") or 0)
    machines = int(payload.get("machines") or 0)
    rows = payload.get("data")
    if jobs <= 0 or machines <= 0:
        raise ValueError("ScheduleOpt JSPLIB JSON requires positive jobs and machines")
    if not isinstance(rows, list):
        raise ValueError("ScheduleOpt JSPLIB JSON data must be a list")

    operations: list[JobShopOperation] = []
    seen: set[tuple[int, int]] = set()
    for raw in rows:
        if not isinstance(raw, dict):
            raise ValueError("ScheduleOpt JSPLIB JSON operation rows must be objects")
        operation = JobShopOperation(
            job=int(raw["job"]),
            operation=int(raw["operation"]),
            machine=int(raw["machine"]),
            duration=int(raw["duration"]),
        )
        if operation.job < 0 or operation.job >= jobs:
            raise ValueError(f"operation job index out of range: {operation.job}")
        if operation.operation < 0 or operation.operation >= machines:
            raise ValueError(f"operation index out of range: {operation.operation}")
        if operation.machine < 0 or operation.machine >= machines:
            raise ValueError(f"operation machine index out of range: {operation.machine}")
        if operation.duration < 0:
            raise ValueError(f"operation duration must be non-negative: {operation.duration}")
        key = (operation.job, operation.operation)
        if key in seen:
            raise ValueError(f"duplicate operation for job/order pair: {key}")
        seen.add(key)
        operations.append(operation)

    expected_count = jobs * machines
    if len(operations) != expected_count:
        raise ValueError(f"expected {expected_count} operations, found {len(operations)}")
    expected_pairs = {(job, operation) for job in range(jobs) for operation in range(machines)}
    missing_pairs = expected_pairs - seen
    if missing_pairs:
        missing = sorted(missing_pairs)[:5]
        raise ValueError(f"missing job/order operation pairs: {missing}")

    return JobShopInstance(
        name=name,
        jobs=jobs,
        machines=machines,
        operations=tuple(sorted(operations, key=lambda item: (item.job, item.operation))),
        family=str(payload["family"]) if payload.get("family") is not None else None,
        family_long=str(payload["family_long"]) if payload.get("family_long") is not None else None,
        year=str(payload["year"]) if payload.get("year") is not None else None,
    )


def load_job_shop_case(
    case: dict[str, Any],
    *,
    cache_dir: str | Path = RAW_DIR,
    allow_download: bool = True,
) -> JobShopInstance:
    data = case.get("data", {})
    local_path = data.get("local_path")
    if local_path:
        return parse_scheduleopt_jsplib_json(Path(local_path).read_text(encoding="utf-8"))

    instance_name = str(case.get("instance") or case["benchmark_id"].removeprefix("jsplib_"))
    path = Path(str(data.get("raw_path") or "")) if data.get("raw_path") else Path(cache_dir) / f"{instance_name}.json"
    if path.exists():
        return parse_scheduleopt_jsplib_json(path.read_text(encoding="utf-8"))

    urls = [str(url) for url in [data.get("instance_url"), *data.get("mirror_urls", [])] if url]
    if not urls:
        raise ValueError(f"case {case['benchmark_id']} does not provide an instance_url")
    if not allow_download:
        raise FileNotFoundError(f"cached JSPLIB file not found and downloads are disabled: {path}")

    path.parent.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    for url in urls:
        try:
            text = _download_text(url)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            errors.append(f"{url}: {type(exc).__name__}: {exc}")
            continue
        path.write_text(text, encoding="utf-8")
        return parse_scheduleopt_jsplib_json(text)
    raise RuntimeError(
        f"failed to download JSPLIB case {case['benchmark_id']} from {len(urls)} source(s): "
        + " | ".join(errors)
    )


def _download_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": "optagent-benchmark/1.0"})
    with urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", errors="replace")

def machine_order_from_solution(context: dict[str, Any], variable_values: dict[int, Any]) -> dict[int, list[tuple[int, int]]]:
    machine_orders: dict[int, list[tuple[int, int]]] = {}
    for machine, sequence_node_id in context["machine_sequence_node_ids"].items():
        local_order = [int(item) for item in variable_values.get(sequence_node_id, [])]
        keys = context["machine_operation_keys"][machine]
        machine_orders[machine] = [keys[index] for index in local_order if 0 <= index < len(keys)]
    return machine_orders


def makespan_from_solution(context: dict[str, Any], variable_values: dict[int, Any]) -> int | None:
    ends: list[int] = []
    for node_id in context["operation_node_ids"].values():
        raw = variable_values.get(node_id)
        if not isinstance(raw, dict) or "end" not in raw:
            return None
        ends.append(int(raw["end"]))
    return max(ends) if ends else None


def _operation_key(operation: JobShopOperation) -> tuple[int, int]:
    return (int(operation.job), int(operation.operation))


def _solution_objective(
    context: dict[str, Any],
    variable_values: dict[int, Any],
    solution_objective: float | None,
) -> float | None:
    if solution_objective is not None:
        return float(solution_objective)
    makespan = makespan_from_solution(context, variable_values)
    return float(makespan) if makespan is not None else None


def _decoded_machine_orders(context: dict[str, Any], variable_values: dict[int, Any]) -> dict[str, list[list[int]]]:
    orders = machine_order_from_solution(context, variable_values)
    return {
        str(machine): [[job, operation] for job, operation in order]
        for machine, order in sorted(orders.items())
    }
