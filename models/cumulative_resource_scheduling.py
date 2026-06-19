from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from optagent import ModelBuilder

from benchmarks.loaders.cumulative_resource_scheduling import RcpspInstance


@dataclass(frozen=True)
class RcpspBenchmarkModel:
    program: Any
    activity_node_ids: dict[int, int]
    objective_node_id: int
    horizon: int
    instance: RcpspInstance


def build_rcpsp_model(case: dict[str, Any], instance: RcpspInstance) -> RcpspBenchmarkModel:
    horizon = max(0, instance.horizon)
    builder = ModelBuilder(
        metadata={
            "benchmark_id": case["benchmark_id"],
            "family": "cumulative_resource_scheduling",
            "model_style": "interval_var_cumulative_precedence",
            "source": "PSPLIB via ScheduleOpt",
            "activities": instance.activity_count,
            "non_dummy_activities": instance.non_dummy_activity_count,
            "renewable_resources": instance.resource_count,
            "horizon": horizon,
        }
    )

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
        builder.constraint(
            builder.cumulative(intervals, demands, builder.const(capacity)),
            name=f"resource_{resource_id + 1}_capacity",
        )

    objective = builder.minimize(
        builder.interval_end(activity_vars[instance.sink_activity_id]),
        name="makespan",
    )
    return RcpspBenchmarkModel(
        program=builder.freeze(),
        activity_node_ids=activity_node_ids,
        objective_node_id=objective.node_id,
        horizon=horizon,
        instance=instance,
    )


def makespan_from_solution(model: RcpspBenchmarkModel, variable_values: dict[int, Any]) -> int | None:
    sink = variable_values.get(model.activity_node_ids[model.instance.sink_activity_id])
    if not isinstance(sink, dict) or "end" not in sink:
        return None
    return int(sink["end"])


def activity_start_head(model: RcpspBenchmarkModel, variable_values: dict[int, Any], *, limit: int = 20) -> list[dict[str, int]]:
    rows: list[dict[str, int]] = []
    for activity_id in sorted(model.activity_node_ids)[:limit]:
        raw = variable_values.get(model.activity_node_ids[activity_id])
        if isinstance(raw, dict) and "start" in raw and "end" in raw:
            rows.append({"activity": activity_id + 1, "start": int(raw["start"]), "end": int(raw["end"])})
    return rows
