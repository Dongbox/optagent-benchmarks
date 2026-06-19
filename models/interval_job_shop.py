from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from optagent import ModelBuilder

from benchmarks.loaders.interval_job_shop import JobShopInstance, JobShopOperation


@dataclass(frozen=True)
class JobShopBenchmarkModel:
    program: Any
    operation_node_ids: dict[tuple[int, int], int]
    machine_sequence_node_ids: dict[int, int]
    machine_operation_keys: dict[int, tuple[tuple[int, int], ...]]
    objective_node_id: int
    horizon: int
    instance: JobShopInstance


def build_job_shop_model(case: dict[str, Any], instance: JobShopInstance) -> JobShopBenchmarkModel:
    horizon = max(0, instance.horizon)
    builder = ModelBuilder(
        metadata={
            "benchmark_id": case["benchmark_id"],
            "family": "interval_job_shop",
            "model_style": "interval_var_sequence_no_overlap_precedence",
            "source": "JSPLIB via ScheduleOpt",
            "jobs": instance.jobs,
            "machines": instance.machines,
            "operations": instance.operation_count,
            "horizon": horizon,
        }
    )

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
        sequence = builder.sequence_var(
            size=len(keys),
            default=list(range(len(keys))),
            name=f"machine_{machine}_order",
        )
        machine_sequence_node_ids[machine] = sequence.node_id
        machine_operation_keys[machine] = keys
        builder.constraint(
            builder.no_overlap(sequence, *(operation_vars[key] for key in keys)),
            name=f"machine_{machine}_capacity",
        )

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
    return JobShopBenchmarkModel(
        program=builder.freeze(),
        operation_node_ids=operation_node_ids,
        machine_sequence_node_ids=machine_sequence_node_ids,
        machine_operation_keys=machine_operation_keys,
        objective_node_id=objective.node_id,
        horizon=horizon,
        instance=instance,
    )


def machine_order_from_solution(
    model: JobShopBenchmarkModel,
    variable_values: dict[int, Any],
) -> dict[int, list[tuple[int, int]]]:
    machine_orders: dict[int, list[tuple[int, int]]] = {}
    for machine, sequence_node_id in model.machine_sequence_node_ids.items():
        local_order = [int(item) for item in variable_values.get(sequence_node_id, [])]
        keys = model.machine_operation_keys[machine]
        machine_orders[machine] = [keys[index] for index in local_order if 0 <= index < len(keys)]
    return machine_orders


def makespan_from_solution(model: JobShopBenchmarkModel, variable_values: dict[int, Any]) -> int | None:
    ends: list[int] = []
    for node_id in model.operation_node_ids.values():
        raw = variable_values.get(node_id)
        if not isinstance(raw, dict) or "end" not in raw:
            return None
        ends.append(int(raw["end"]))
    return max(ends) if ends else None


def _operation_key(operation: JobShopOperation) -> tuple[int, int]:
    return (int(operation.job), int(operation.operation))
