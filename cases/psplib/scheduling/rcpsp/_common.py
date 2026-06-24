from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from optagent import ModelBuilder

from benchmarks.cases.base import BenchmarkCase

SOURCE = "PSPLIB j90 via ScheduleOpt"
SOURCE_KEY = "psplib"
PROBLEM_TYPE = "scheduling"
INSTANCE_TYPE = "rcpsp"
FAMILY = "cumulative_resource_scheduling"
MODEL_STYLE = "interval_var_cumulative_precedence"
RAW_DIR = Path(__file__).resolve().parent / "raw"


@dataclass(frozen=True)
class RcpspActivity:
    activity_id: int
    duration: int
    demands: tuple[int, ...]
    successors: tuple[int, ...]


@dataclass(frozen=True)
class RcpspInstance:
    name: str
    activity_count: int
    resource_count: int
    capacities: tuple[int, ...]
    activities: tuple[RcpspActivity, ...]

    @property
    def non_dummy_activity_count(self) -> int:
        return max(0, self.activity_count - 2)

    @property
    def horizon(self) -> int:
        return sum(activity.duration for activity in self.activities)

    @property
    def source_activity_id(self) -> int:
        return 0

    @property
    def sink_activity_id(self) -> int:
        return self.activity_count - 1


class RcpspCase(BenchmarkCase):
    def build_model(self, **kwargs: Any) -> ModelBuilder:
        allow_download = bool(kwargs.get("allow_download", True))
        instance = load_rcpsp_case(self.to_row(), cache_dir=RAW_DIR, allow_download=allow_download)
        horizon = max(0, instance.horizon)
        builder = ModelBuilder(metadata={"model_style": MODEL_STYLE})
        activity_vars: dict[int, Any] = {}
        activity_node_ids: dict[int, int] = {}
        for activity in instance.activities:
            interval = builder.interval_var(
                start=0,
                length=activity.duration,
                lb_start=0,
                ub_start=horizon,
                lb_length=activity.duration,
                ub_length=activity.duration,
                name=f"activity_{activity.activity_id + 1}",
            )
            activity_vars[activity.activity_id] = interval
            activity_node_ids[activity.activity_id] = interval.node_id
        for activity in instance.activities:
            before = activity_vars[activity.activity_id]
            for successor_id in activity.successors:
                builder.constraint(
                    builder.precedence(before, activity_vars[successor_id], lag=0),
                    name=f"activity_{activity.activity_id + 1}_before_{successor_id + 1}",
                )
        for resource_id, capacity in enumerate(instance.capacities):
            intervals = []
            demands = []
            for activity in instance.activities:
                demand = activity.demands[resource_id]
                if demand <= 0 or activity.duration <= 0:
                    continue
                intervals.append(activity_vars[activity.activity_id])
                demands.append(builder.const(demand))
            builder.constraint(builder.cumulative(intervals, demands, builder.const(capacity)), name=f"resource_{resource_id + 1}_capacity")
        objective = builder.minimize(builder.interval_end(activity_vars[instance.sink_activity_id]), name="makespan")
        self._set_build_context(
            {
                "instance": instance,
                "activity_node_ids": activity_node_ids,
                "objective_node_id": objective.node_id,
                "horizon": horizon,
            }
        )
        return builder

    def solution_summary(self, solution: Any, **kwargs: Any) -> dict[str, Any]:
        context = self._build_context()
        raw_objective = _solution_objective(context, solution.variable_values, solution.objective_value)
        objective = raw_objective if solution.feasible else None
        instance = context["instance"]
        return {
            **super().solution_summary(solution, **kwargs),
            "objective": float(objective) if objective is not None else None,
            "raw_objective": float(raw_objective) if raw_objective is not None else None,
            "dimension": instance.activity_count,
            "edge_weight_type": "rcpsp_cumulative",
            "model_style": MODEL_STYLE,
            "activity_start_head": activity_start_head(context, solution.variable_values),
            "metadata": {
                **dict(getattr(solution, "metadata", {}) or {}),
                "activities": instance.activity_count,
                "renewable_resources": instance.resource_count,
                "horizon": context["horizon"],
            },
        }


def parse_psplib_rcp_text(text: str, *, name: str) -> RcpspInstance:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 2:
        raise ValueError("PSPLIB .rcp data requires a header and capacity row")

    header = [int(item) for item in lines[0].split()]
    if len(header) != 2:
        raise ValueError("PSPLIB .rcp first row must contain activity count and resource count")
    activity_count, resource_count = header
    if activity_count <= 0 or resource_count <= 0:
        raise ValueError("PSPLIB .rcp activity and resource counts must be positive")

    capacities = tuple(int(item) for item in lines[1].split())
    if len(capacities) != resource_count:
        raise ValueError(f"expected {resource_count} resource capacities, found {len(capacities)}")

    activity_lines = lines[2:]
    if len(activity_lines) != activity_count:
        raise ValueError(f"expected {activity_count} activity rows, found {len(activity_lines)}")

    activities: list[RcpspActivity] = []
    for activity_id, line in enumerate(activity_lines):
        values = [int(item) for item in line.split()]
        minimum = 1 + resource_count + 1
        if len(values) < minimum:
            raise ValueError(f"activity row {activity_id + 1} is too short")
        duration = values[0]
        demands = tuple(values[1 : 1 + resource_count])
        successor_count = values[1 + resource_count]
        successor_values = values[2 + resource_count :]
        if len(successor_values) != successor_count:
            raise ValueError(
                f"activity row {activity_id + 1} declares {successor_count} successors "
                f"but provides {len(successor_values)}"
            )
        successors = tuple(successor - 1 for successor in successor_values)
        if duration < 0:
            raise ValueError(f"activity {activity_id + 1} duration must be non-negative")
        if any(demand < 0 for demand in demands):
            raise ValueError(f"activity {activity_id + 1} demands must be non-negative")
        for successor in successors:
            if successor < 0 or successor >= activity_count:
                raise ValueError(f"activity {activity_id + 1} successor out of range: {successor + 1}")
        activities.append(
            RcpspActivity(
                activity_id=activity_id,
                duration=duration,
                demands=demands,
                successors=successors,
            )
        )

    return RcpspInstance(
        name=name,
        activity_count=activity_count,
        resource_count=resource_count,
        capacities=capacities,
        activities=tuple(activities),
    )


def load_rcpsp_case(
    case: dict[str, Any],
    *,
    cache_dir: str | Path = RAW_DIR,
    allow_download: bool = True,
) -> RcpspInstance:
    data = case.get("data", {})
    instance_name = str(case.get("instance") or case["benchmark_id"].removeprefix("psplib_"))
    local_path = data.get("local_path")
    if local_path:
        return parse_psplib_rcp_text(Path(local_path).read_text(encoding="utf-8"), name=instance_name)

    path = Path(cache_dir) / f"{instance_name}.rcp"
    if path.exists():
        return parse_psplib_rcp_text(path.read_text(encoding="utf-8"), name=instance_name)

    urls = [str(url) for url in [data.get("instance_url"), *data.get("mirror_urls", [])] if url]
    if not urls:
        raise ValueError(f"case {case['benchmark_id']} does not provide an instance_url")
    if not allow_download:
        raise FileNotFoundError(f"cached PSPLIB file not found and downloads are disabled: {path}")

    path.parent.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    for url in urls:
        try:
            text = _download_text(url)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            errors.append(f"{url}: {type(exc).__name__}: {exc}")
            continue
        path.write_text(text, encoding="utf-8")
        return parse_psplib_rcp_text(text, name=instance_name)
    raise RuntimeError(
        f"failed to download PSPLIB case {case['benchmark_id']} from {len(urls)} source(s): "
        + " | ".join(errors)
    )


def _download_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": "optagent-benchmark/1.0"})
    with urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", errors="replace")

def makespan_from_solution(context: dict[str, Any], variable_values: dict[int, Any]) -> int | None:
    instance = context["instance"]
    sink = variable_values.get(context["activity_node_ids"][instance.sink_activity_id])
    if not isinstance(sink, dict) or "end" not in sink:
        return None
    return int(sink["end"])


def activity_start_head(context: dict[str, Any], variable_values: dict[int, Any], *, limit: int = 20) -> list[dict[str, int]]:
    rows: list[dict[str, int]] = []
    for activity_id in sorted(context["activity_node_ids"])[:limit]:
        raw = variable_values.get(context["activity_node_ids"][activity_id])
        if isinstance(raw, dict) and "start" in raw and "end" in raw:
            rows.append({"activity": activity_id + 1, "start": int(raw["start"]), "end": int(raw["end"])})
    return rows


def _solution_objective(
    context: dict[str, Any],
    variable_values: dict[int, Any],
    solution_objective: float | None,
) -> float | None:
    if solution_objective is not None:
        return float(solution_objective)
    makespan = makespan_from_solution(context, variable_values)
    return float(makespan) if makespan is not None else None
