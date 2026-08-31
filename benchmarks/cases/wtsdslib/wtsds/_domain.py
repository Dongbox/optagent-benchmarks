from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from optagent import ModelBuilder, SchedulingModel

from benchmarks.cases.base import BenchmarkCase, SolutionVerification, verify_interval, verify_permutation

SOURCE = "WTSDS by Cicirello"
SOURCE_KEY = "wtsdslib"
PROBLEM_TYPE = "scheduling"
INSTANCE_TYPE = "weighted_tardiness_sequence_dependent_setups"
FAMILY = "sequence_weighted_tardiness_scheduling"
MODEL_STYLE = "interval_var_sequence_setup_weighted_tardiness"
RAW_DIR = Path(__file__).resolve().parent / "raw"
INSTANCE_DIR = RAW_DIR / "wtsds-instances"
REFERENCE_PATH = RAW_DIR / "CicirelloSolution - CicirelloSolution.csv"
INSTANCE_URL = "https://www.cicirello.org/datasets/wtsds/"
REFERENCE_URL = "https://sites.google.com/site/shunjitanaka/smtwtss"
JOB_COUNT = 60
INSTANCE_COUNT = 120


@dataclass(frozen=True)
class WtsdsInstance:
    name: str
    jobs: int
    processing_times: tuple[int, ...]
    weights: tuple[int, ...]
    due_dates: tuple[int, ...]
    initial_setup: tuple[int, ...]
    setup_times: tuple[tuple[int, ...], ...]

    @property
    def horizon(self) -> int:
        largest_setup = max((*self.initial_setup, *(value for row in self.setup_times for value in row)), default=0)
        return sum(self.processing_times) + (self.jobs * largest_setup)

    def weighted_tardiness(self, order: list[int] | tuple[int, ...]) -> int:
        if len(order) != self.jobs or set(order) != set(range(self.jobs)):
            raise ValueError(f"WTSDS order must be a permutation of 0..{self.jobs - 1}")
        completion = 0
        total = 0
        previous: int | None = None
        for job in order:
            setup = self.initial_setup[job] if previous is None else self.setup_times[previous][job]
            completion += setup + self.processing_times[job]
            total += self.weights[job] * max(0, completion - self.due_dates[job])
            previous = job
        return int(total)


class WtsdsCase(BenchmarkCase):
    def build_model(self, **kwargs: Any) -> ModelBuilder:
        allow_download = bool(kwargs.get("allow_download", True))
        instance = load_wtsds_case(self.to_row(), cache_dir=RAW_DIR, allow_download=allow_download)
        builder = ModelBuilder(metadata={"model_style": MODEL_STYLE})
        scheduling = SchedulingModel(builder, horizon=instance.horizon)
        machine = scheduling.unary_resource("machine")
        tasks = []
        intervals: dict[int, Any] = {}
        interval_node_ids: dict[int, int] = {}

        for job in range(instance.jobs):
            task = scheduling.task(f"job_{job}")
            task.due_at(instance.due_dates[job])
            alternative = task.alternative(
                resource=machine,
                duration=instance.processing_times[job],
                optional=False,
            )
            tasks.append(task)
            intervals[job] = alternative.interval
            interval_node_ids[job] = alternative.interval.node_id

        machine.no_overlap(name="machine_no_overlap")
        sequence = machine.sequence()
        sequence.view(name="machine_sequence").setup_time(
            item_types={task: job for job, task in enumerate(tasks)},
            transitions={
                (before, after): instance.setup_times[before][after]
                for before in range(instance.jobs)
                for after in range(instance.jobs)
            },
            start_type="initial",
            start_transitions={job: instance.initial_setup[job] for job in range(instance.jobs)},
            name="sequence_dependent_setup",
        )
        weighted_tardiness = builder.sum(
            *(instance.weights[job] * tasks[job].tardiness() for job in range(instance.jobs))
        )
        objective = builder.minimize(weighted_tardiness, name="total_weighted_tardiness")
        scheduling.validate()
        self._set_build_context(
            {
                "instance": instance,
                "interval_node_ids": interval_node_ids,
                "sequence_node_id": sequence.expr.node_id,
                "objective_node_id": objective.node_id,
                "horizon": instance.horizon,
            }
        )
        return builder

    def solution_metrics(self, solution: Any, **kwargs: Any) -> dict[str, Any]:
        context = self._build_context()
        instance = context["instance"]
        raw_objective = _solution_objective(context, solution.variable_values, solution.objective_value)
        objective = raw_objective if solution.feasible else None
        return {
            "objective": float(objective) if objective is not None else None,
            "raw_objective": float(raw_objective) if raw_objective is not None else None,
            "model_style": MODEL_STYLE,
            "decoded_solution": {
                "kind": "weighted_tardiness_schedule",
                "job_order": job_order_from_solution(context, solution.variable_values),
                "job_intervals": job_intervals_from_solution(context, solution.variable_values),
            },
            "metadata": {"jobs": instance.jobs, "horizon": context["horizon"]},
        }

    def verify_solution(self, solution: Any, **kwargs: Any) -> SolutionVerification:
        context = self._build_context()
        instance = context["instance"]
        order, order_errors = verify_permutation(
            solution.variable_values.get(context["sequence_node_id"]),
            size=instance.jobs,
            label="machine order",
        )
        violations = list(order_errors)
        intervals: dict[int, tuple[int, int]] = {}
        for job in range(instance.jobs):
            interval, errors = verify_interval(
                solution.variable_values.get(context["interval_node_ids"][job]),
                duration=instance.processing_times[job],
                label=f"job {job}",
            )
            violations.extend(errors)
            if interval is not None:
                intervals[job] = interval
        if order is not None:
            previous: int | None = None
            for job in order:
                current = intervals.get(job)
                if current is None:
                    previous = job
                    continue
                required_start = instance.initial_setup[job]
                if previous is not None:
                    predecessor = intervals.get(previous)
                    if predecessor is None:
                        previous = job
                        continue
                    required_start = predecessor[1] + instance.setup_times[previous][job]
                if current[0] < required_start:
                    violations.append(f"job {job} starts before its required sequence setup finishes")
                previous = job
        if violations:
            return SolutionVerification.failed(*violations)
        objective = sum(
            instance.weights[job] * max(0, intervals[job][1] - instance.due_dates[job])
            for job in range(instance.jobs)
        )
        return SolutionVerification.accepted(objective=float(objective))


def load_wtsds_references(path: str | Path = REFERENCE_PATH) -> dict[int, tuple[int, tuple[int, ...]]]:
    """Read the published objective and zero-based job order for every WTSDS instance."""

    references: dict[int, tuple[int, tuple[int, ...]]] = {}
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            number = int(row["No"])
            objective = int(row["opt"])
            order = tuple(int(row[str(job + 1)]) for job in range(JOB_COUNT))
            if number in references:
                raise ValueError(f"duplicate WTSDS reference row: {number}")
            if set(order) != set(range(JOB_COUNT)):
                raise ValueError(f"WTSDS reference row {number} is not a 0..{JOB_COUNT - 1} permutation")
            references[number] = (objective, order)
    expected = set(range(1, INSTANCE_COUNT + 1))
    if set(references) != expected:
        raise ValueError("WTSDS reference CSV does not contain exactly the 120 published instances")
    return references


def make_wtsds_cases(*, case_module: str) -> tuple[WtsdsCase, ...]:
    references = load_wtsds_references()
    return tuple(
        make_wtsds_case(
            number=number,
            objective=objective,
            reference_order=order,
            case_module=case_module,
        )
        for number, (objective, order) in sorted(references.items())
    )


def make_wtsds_case(
    *,
    number: int,
    objective: int,
    reference_order: tuple[int, ...],
    case_module: str,
) -> WtsdsCase:
    instance = f"wt_sds_{number}"
    compare_key = f"{SOURCE_KEY}/{PROBLEM_TYPE}/{INSTANCE_TYPE}/{instance}"
    return WtsdsCase(
        benchmark_id=f"{SOURCE_KEY}_{instance}",
        source=SOURCE,
        problem_type=PROBLEM_TYPE,
        instance_type=INSTANCE_TYPE,
        instance=instance,
        family=FAMILY,
        tier="calibration",
        compare_key=compare_key,
        series_key=f"{compare_key}/{MODEL_STYLE}",
        size={"jobs": JOB_COUNT},
        data={
            "raw_path": str(INSTANCE_DIR / f"{instance}.instance"),
            "reference_raw_path": str(REFERENCE_PATH),
            "instance_url": INSTANCE_URL,
            "reference_url": REFERENCE_URL,
        },
        reference={
            "objective": objective,
            "sequence": list(reference_order),
            "source_label": "Tanaka and Araki optimal solution",
            "source_url": REFERENCE_URL,
            "status": "optimal",
            "value_kind": "optimal",
        },
        problem_description=(
            f"WTSDS instance {instance}: sequence {JOB_COUNT} jobs on one machine with sequence-dependent "
            "setups to minimize total weighted tardiness."
        ),
        case_module=case_module,
        modeling_notes={
            "model_style": MODEL_STYLE,
            "objective_sense": "minimize",
            "public_api_primitives": ["interval_var", "sequence_var", "no_overlap", "sequence_setup", "max"],
        },
    )


def parse_wtsds_text(text: str, *, name: str) -> WtsdsInstance:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    jobs = _header_int(lines, "Problem Size:")
    if jobs <= 0:
        raise ValueError("WTSDS problem size must be positive")
    processing_times = _integer_section(lines, "Process Times:", "Weights:")
    weights = _integer_section(lines, "Weights:", "Duedates:")
    due_dates = _integer_section(lines, "Duedates:", "Setup Times:")
    if any(len(values) != jobs for values in (processing_times, weights, due_dates)):
        raise ValueError(f"WTSDS instance {name!r} requires exactly {jobs} processing times, weights, and due dates")
    if any(value < 0 for value in processing_times):
        raise ValueError("WTSDS processing times must be non-negative")
    if any(value < 0 for value in weights):
        raise ValueError("WTSDS weights must be non-negative")

    setup_rows = _setup_rows(lines, "Setup Times:")
    expected_setup_keys = {(-1, job) for job in range(jobs)} | {
        (before, after) for before in range(jobs) for after in range(jobs) if before != after
    }
    if set(setup_rows) != expected_setup_keys:
        raise ValueError(f"WTSDS instance {name!r} has incomplete or invalid setup-time rows")
    if any(value < 0 for value in setup_rows.values()):
        raise ValueError("WTSDS setup times must be non-negative")
    return WtsdsInstance(
        name=name,
        jobs=jobs,
        processing_times=tuple(processing_times),
        weights=tuple(weights),
        due_dates=tuple(due_dates),
        initial_setup=tuple(setup_rows[-1, job] for job in range(jobs)),
        setup_times=tuple(
            tuple(0 if before == after else setup_rows[before, after] for after in range(jobs))
            for before in range(jobs)
        ),
    )


def load_wtsds_case(
    case: dict[str, Any],
    *,
    cache_dir: str | Path = RAW_DIR,
    allow_download: bool = True,
) -> WtsdsInstance:
    data = case.get("data", {})
    instance_name = str(case.get("instance") or case["benchmark_id"].removeprefix(f"{SOURCE_KEY}_"))
    local_path = data.get("local_path")
    if local_path:
        return parse_wtsds_text(Path(local_path).read_text(encoding="utf-8"), name=instance_name)
    path = Path(str(data.get("raw_path") or "")) if data.get("raw_path") else Path(cache_dir) / f"{instance_name}.instance"
    if path.exists():
        return parse_wtsds_text(path.read_text(encoding="utf-8"), name=instance_name)
    if not allow_download:
        raise FileNotFoundError(f"cached WTSDS file not found and downloads are disabled: {path}")
    raise FileNotFoundError(f"cached WTSDS file not found: {path}")


def job_order_from_solution(context: dict[str, Any], variable_values: dict[int, Any]) -> list[int]:
    raw = variable_values.get(context["sequence_node_id"], [])
    return [int(job) for job in raw] if isinstance(raw, (list, tuple)) else []


def job_intervals_from_solution(context: dict[str, Any], variable_values: dict[int, Any]) -> list[dict[str, int]]:
    rows: list[dict[str, int]] = []
    for job, node_id in sorted(context["interval_node_ids"].items()):
        raw = variable_values.get(node_id)
        if isinstance(raw, dict) and {"start", "end"}.issubset(raw):
            rows.append({"job": job, "start": int(raw["start"]), "end": int(raw["end"])})
    return rows


def _solution_objective(
    context: dict[str, Any],
    variable_values: dict[int, Any],
    solution_objective: float | None,
) -> float | None:
    instance = context["instance"]
    intervals = job_intervals_from_solution(context, variable_values)
    if len(intervals) == instance.jobs:
        return float(
            sum(
                instance.weights[row["job"]] * max(0, row["end"] - instance.due_dates[row["job"]])
                for row in intervals
            )
        )
    return float(solution_objective) if solution_objective is not None else None


def _header_int(lines: list[str], header: str) -> int:
    for line in lines:
        if line.startswith(header):
            return int(line.removeprefix(header).strip())
    raise ValueError(f"WTSDS data is missing {header!r}")


def _integer_section(lines: list[str], header: str, next_header: str) -> list[int]:
    start = _header_index(lines, header) + 1
    end = _header_index(lines, next_header)
    return [int(line) for line in lines[start:end]]


def _setup_rows(lines: list[str], header: str) -> dict[tuple[int, int], int]:
    start = _header_index(lines, header) + 1
    rows: dict[tuple[int, int], int] = {}
    for line in lines[start:]:
        if line == "End Problem Specification":
            break
        values = [int(value) for value in line.split()]
        if len(values) != 3:
            raise ValueError(f"invalid WTSDS setup-time row: {line!r}")
        key = (values[0], values[1])
        if key in rows:
            raise ValueError(f"duplicate WTSDS setup-time row: {key}")
        rows[key] = values[2]
    return rows


def _header_index(lines: list[str], header: str) -> int:
    try:
        return lines.index(header)
    except ValueError as exc:
        raise ValueError(f"WTSDS data is missing {header!r}") from exc
