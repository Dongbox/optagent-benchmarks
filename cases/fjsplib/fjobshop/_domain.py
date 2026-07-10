from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from optagent import ModelBuilder

from benchmarks.cases.base import BenchmarkCase

SOURCE = "FJSPLIB flexible job-shop"
SOURCE_KEY = "fjsplib"
PROBLEM_TYPE = "scheduling"
INSTANCE_TYPE = "fjobshop"
FAMILY = "flexible_interval_job_shop"
MODEL_STYLE = "optional_interval_machine_choice_no_overlap_precedence"
RAW_DIR = Path(__file__).resolve().parent / "raw"
REFERENCE_SOURCE_URL = "https://github.com/SchedulingLab/fjsp-instances"


@dataclass(frozen=True)
class FlexibleJobShopCandidate:
    operation_id: int
    machine: int
    duration: int


@dataclass(frozen=True)
class FlexibleJobShopOperation:
    operation_id: int
    job: int
    operation: int
    candidates: tuple[FlexibleJobShopCandidate, ...]


@dataclass(frozen=True)
class FlexibleJobShopInstance:
    name: str
    jobs: int
    machines: int
    operations: tuple[FlexibleJobShopOperation, ...]
    reference: dict[str, Any]
    source_format: str = "fjsplib_json"

    @property
    def operation_count(self) -> int:
        return len(self.operations)

    @property
    def candidate_count(self) -> int:
        return sum(len(operation.candidates) for operation in self.operations)

    @property
    def flexibility(self) -> float:
        if not self.operations:
            return 0.0
        return self.candidate_count / len(self.operations)

    @property
    def horizon(self) -> int:
        return sum(max(candidate.duration for candidate in operation.candidates) for operation in self.operations)

    def operations_by_job(self) -> dict[int, tuple[FlexibleJobShopOperation, ...]]:
        grouped: dict[int, list[FlexibleJobShopOperation]] = {job: [] for job in range(self.jobs)}
        for operation in self.operations:
            grouped.setdefault(operation.job, []).append(operation)
        return {
            job: tuple(sorted(items, key=lambda item: item.operation))
            for job, items in sorted(grouped.items())
        }


class FlexibleJobShopCase(BenchmarkCase):
    def build_model(self, **kwargs: Any) -> ModelBuilder:
        allow_download = bool(kwargs.get("allow_download", True))
        instance = load_flexible_job_shop_case(self.to_row(), cache_dir=RAW_DIR, allow_download=allow_download)
        horizon = max(0, instance.horizon)
        builder = ModelBuilder(metadata={"model_style": MODEL_STYLE})

        choose_vars: dict[tuple[int, int], Any] = {}
        optional_intervals: dict[tuple[int, int], Any] = {}
        selected_starts: dict[int, Any] = {}
        selected_ends: dict[int, Any] = {}
        interval_node_ids: dict[tuple[int, int], int] = {}
        choice_node_ids: dict[tuple[int, int], int] = {}
        machine_to_intervals: dict[int, list[Any]] = {machine: [] for machine in range(instance.machines)}
        machine_candidate_keys: dict[int, list[tuple[int, int]]] = {machine: [] for machine in range(instance.machines)}

        for operation in instance.operations:
            if not operation.candidates:
                raise ValueError(f"operation {operation.operation_id} has no machine candidates")
            for local_index, candidate in enumerate(operation.candidates):
                key = (operation.operation_id, candidate.machine)
                presence = builder.bool_var(
                    default=local_index == 0,
                    name=f"choose_op{operation.operation_id}_m{candidate.machine}",
                )
                interval = builder.optional_interval_var(
                    start=0,
                    length=candidate.duration,
                    lb_start=0,
                    ub_start=horizon,
                    lb_length=candidate.duration,
                    ub_length=candidate.duration,
                    presence=presence,
                    name=f"op{operation.operation_id}_j{operation.job}_k{operation.operation}_m{candidate.machine}",
                )
                choose_vars[key] = presence
                optional_intervals[key] = interval
                choice_node_ids[key] = presence.node_id
                interval_node_ids[key] = interval.node_id
                machine_to_intervals.setdefault(candidate.machine, []).append(interval)
                machine_candidate_keys.setdefault(candidate.machine, []).append(key)

        for operation in instance.operations:
            choice_terms = [
                choose_vars[(operation.operation_id, candidate.machine)]
                for candidate in operation.candidates
            ]
            interval_terms = [
                optional_intervals[(operation.operation_id, candidate.machine)]
                for candidate in operation.candidates
            ]
            builder.constraint(
                builder.exactly_one(*choice_terms),
                name=f"op{operation.operation_id}_choose_one_machine",
            )
            selected_starts[operation.operation_id] = builder.selected_start(interval_terms, choice_terms)
            selected_ends[operation.operation_id] = builder.selected_end(interval_terms, choice_terms)

        machine_sequence_node_ids: dict[int, int] = {}
        for machine, intervals in sorted(machine_to_intervals.items()):
            if not intervals:
                continue
            sequence = builder.sequence_var(size=len(intervals), default=list(range(len(intervals))), name=f"machine_{machine}_order")
            machine_sequence_node_ids[machine] = sequence.node_id
            builder.constraint(builder.no_overlap(sequence, *intervals), name=f"machine_{machine}_capacity")

        last_operation_ends = []
        for job, operations in instance.operations_by_job().items():
            for before, after in zip(operations, operations[1:]):
                builder.constraint(
                    selected_ends[before.operation_id] <= selected_starts[after.operation_id],
                    name=f"job_{job}_op_{before.operation}_before_{after.operation}",
                )
            if operations:
                last_operation_ends.append(selected_ends[operations[-1].operation_id])

        if not last_operation_ends:
            raise ValueError(f"FJSP instance {instance.name!r} has no job operations")
        objective = builder.minimize(builder.max(*last_operation_ends), name="makespan")
        self._set_build_context(
            {
                "instance": instance,
                "interval_node_ids": interval_node_ids,
                "choice_node_ids": choice_node_ids,
                "machine_sequence_node_ids": machine_sequence_node_ids,
                "machine_candidate_keys": machine_candidate_keys,
                "objective_node_id": objective.node_id,
                "horizon": horizon,
            }
        )
        return builder

    def solution_metrics(self, solution: Any, **kwargs: Any) -> dict[str, Any]:
        context = self._build_context()
        raw_objective = _solution_objective(context, solution.objective_value)
        objective = raw_objective if solution.feasible else None
        instance = context["instance"]
        return {
            "objective": float(objective) if objective is not None else None,
            "raw_objective": float(raw_objective) if raw_objective is not None else None,
            "model_style": MODEL_STYLE,
            "decoded_solution": {
                "kind": "flexible_job_shop_schedule",
                "selected_machines": _selected_machines_from_solution(context, solution.variable_values),
                "machine_orders": _decoded_machine_orders(context, solution.variable_values),
            },
            "metadata": {
                "jobs": instance.jobs,
                "machines": instance.machines,
                "operations": instance.operation_count,
                "candidates": instance.candidate_count,
                "flexibility": instance.flexibility,
                "horizon": context["horizon"],
            },
        }


def make_flexible_job_shop_case(
    *,
    benchmark_id: str,
    instance: str,
    tier: str,
    jobs: int,
    machines: int,
    operations: int,
    candidates: int,
    raw_path: str | Path,
    objective: int | None = None,
    case_module: str,
    instance_url: str | None = None,
    reference: dict[str, Any] | None = None,
) -> FlexibleJobShopCase:
    compare_key = f"{SOURCE_KEY}/{PROBLEM_TYPE}/{INSTANCE_TYPE}/{instance}"
    effective_reference = _benchmark_reference(reference or {}, objective=objective)

    data: dict[str, Any] = {
        "raw_path": str(raw_path),
        "documentation_url": "https://github.com/SchedulingLab/fjsp-instances",
        "solution_url": str(effective_reference.get("source_url") or REFERENCE_SOURCE_URL),
    }
    if instance_url is not None:
        data["instance_url"] = instance_url

    return FlexibleJobShopCase(
        benchmark_id=benchmark_id,
        source=SOURCE,
        problem_type=PROBLEM_TYPE,
        instance_type=INSTANCE_TYPE,
        instance=instance,
        family=FAMILY,
        tier=tier,
        compare_key=compare_key,
        series_key=f"{compare_key}/{MODEL_STYLE}",
        size={"jobs": jobs, "machines": machines, "operations": operations, "candidates": candidates},
        data=data,
        reference=effective_reference,
        problem_description=(
            f"FJSPLIB flexible job-shop instance {instance}: schedule {jobs} jobs across "
            f"{machines} machines with {operations} operations and {candidates} operation-machine candidates. "
            "Each operation chooses one eligible machine; the objective is minimum makespan."
        ),
        case_module=case_module,
        modeling_notes={
            "model_style": MODEL_STYLE,
            "objective_sense": "minimize",
            "public_api_primitives": [
                "bool_var",
                "optional_interval_var",
                "sequence_var",
                "no_overlap",
                "max",
            ],
        },
    )



def parse_fjsplib_json(text: str, *, name: str) -> FlexibleJobShopInstance:
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("FJSPLIB JSON root must be an object")

    machines = int(payload.get("machines") or 0)
    jobs_payload = payload.get("jobs")
    if machines <= 0:
        raise ValueError("FJSPLIB JSON requires a positive machines value")
    if not isinstance(jobs_payload, list) or not jobs_payload:
        raise ValueError("FJSPLIB JSON requires a non-empty jobs list")

    operations: list[FlexibleJobShopOperation] = []
    operation_id = 0
    for job_index, job_payload in enumerate(jobs_payload):
        if not isinstance(job_payload, list) or not job_payload:
            raise ValueError(f"job {job_index} must contain at least one operation")
        for operation_index, operation_payload in enumerate(job_payload):
            if not isinstance(operation_payload, list) or not operation_payload:
                raise ValueError(f"job {job_index} operation {operation_index} must contain candidates")
            candidates: list[FlexibleJobShopCandidate] = []
            seen_machines: set[int] = set()
            for raw_candidate in operation_payload:
                if not isinstance(raw_candidate, dict):
                    raise ValueError("candidate rows must be objects")
                machine = int(raw_candidate["machine"])
                duration = int(raw_candidate["processing"])
                if machine < 0 or machine >= machines:
                    raise ValueError(f"candidate machine index out of range: {machine}")
                if duration < 0:
                    raise ValueError(f"candidate duration must be non-negative: {duration}")
                if machine in seen_machines:
                    raise ValueError(f"duplicate machine {machine} for job {job_index} operation {operation_index}")
                seen_machines.add(machine)
                candidates.append(
                    FlexibleJobShopCandidate(
                        operation_id=operation_id,
                        machine=machine,
                        duration=duration,
                    )
                )
            operations.append(
                FlexibleJobShopOperation(
                    operation_id=operation_id,
                    job=job_index,
                    operation=operation_index,
                    candidates=tuple(candidates),
                )
            )
            operation_id += 1

    reference = payload.get("reference") if isinstance(payload.get("reference"), dict) else {}
    return FlexibleJobShopInstance(
        name=name,
        jobs=len(jobs_payload),
        machines=machines,
        operations=tuple(operations),
        reference=dict(reference),
    )


def load_fjsplib_json(path: str | Path, *, name: str | None = None) -> FlexibleJobShopInstance:
    path = Path(path)
    return parse_fjsplib_json(path.read_text(encoding="utf-8"), name=name or path.stem)


def load_flexible_job_shop_case(
    case: dict[str, Any],
    *,
    cache_dir: str | Path = RAW_DIR,
    allow_download: bool = True,
) -> FlexibleJobShopInstance:
    data = case.get("data", {})
    instance_name = str(case.get("instance") or case["benchmark_id"].removeprefix("fjsplib_"))
    local_path = data.get("local_path")
    if local_path:
        return load_fjsplib_json(local_path, name=instance_name)

    path = Path(str(data.get("raw_path") or "")) if data.get("raw_path") else Path(cache_dir) / f"{instance_name}.json"
    if path.exists():
        return load_fjsplib_json(path, name=instance_name)

    if not allow_download:
        raise FileNotFoundError(f"cached FJSPLIB file not found and downloads are disabled: {path}")
    raise FileNotFoundError(f"cached FJSPLIB file not found: {path}")


def _benchmark_reference(reference: dict[str, Any], *, objective: int | None) -> dict[str, Any]:
    kind = str(reference.get("kind") or "unknown")
    lower = reference.get("lower_bound")
    upper = reference.get("upper_bound")
    raw_objective = reference.get("objective", objective)
    effective_objective = raw_objective if raw_objective is not None else upper
    if kind == "optimum":
        status = "closed"
        value_kind = "optimal"
    elif kind == "bounds":
        status = "open"
        value_kind = "best_known_upper_bound"
    else:
        status = "unknown"
        value_kind = "unknown"
    result: dict[str, Any] = {
        "source_url": REFERENCE_SOURCE_URL,
        "status": status,
        "value_kind": value_kind,
    }
    if effective_objective is not None:
        result["objective"] = int(effective_objective)
    if lower is not None:
        result["lower_bound"] = int(lower)
    if upper is not None:
        result["upper_bound"] = int(upper)
    return result



def _solution_objective(context: dict[str, Any], solution_objective: float | None) -> float | None:
    if solution_objective is not None:
        return float(solution_objective)
    return None


def _selected_machines_from_solution(context: dict[str, Any], variable_values: dict[int, Any]) -> dict[str, int]:
    selected: dict[str, int] = {}
    for (operation_id, machine), node_id in context["choice_node_ids"].items():
        if bool(variable_values.get(node_id, False)):
            selected[str(operation_id)] = int(machine)
    return selected


def _decoded_machine_orders(context: dict[str, Any], variable_values: dict[int, Any]) -> dict[str, list[list[int]]]:
    decoded: dict[str, list[list[int]]] = {}
    for machine, sequence_node_id in context["machine_sequence_node_ids"].items():
        local_order = [int(item) for item in variable_values.get(sequence_node_id, [])]
        keys = context["machine_candidate_keys"].get(machine, [])
        decoded[str(machine)] = [list(keys[index]) for index in local_order if 0 <= index < len(keys)]
    return decoded

