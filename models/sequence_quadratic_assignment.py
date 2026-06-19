from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from optagent import ExternalCallbackContext, ModelBuilder

from benchmarks.loaders.sequence_quadratic_assignment import QapInstance


@dataclass(frozen=True)
class QapBenchmarkModel:
    program: Any
    assignment_node_id: int
    default_assignment: list[int]
    instance: QapInstance


def build_qap_model(case: dict[str, Any], instance: QapInstance) -> QapBenchmarkModel:
    default_assignment = list(range(instance.size))
    builder = ModelBuilder(
        metadata={
            "benchmark_id": case["benchmark_id"],
            "family": "sequence_quadratic_assignment",
            "model_style": "sequence_var_external_call",
            "source": "QAPLIB",
            "size": instance.size,
        }
    )
    assignment = builder.sequence_var(size=instance.size, default=default_assignment, name="assignment")

    def assignment_cost(ctx: ExternalCallbackContext) -> int:
        candidate = [int(item) for item in ctx.value(assignment)]
        return instance.assignment_cost(candidate)

    builder.minimize(
        builder.external_call(
            assignment_cost,
            name="assignment_cost",
            pure=True,
            deterministic=True,
            cacheable=True,
            timeout_ms=100,
            depends_on=(assignment,),
        ),
        name="assignment_cost",
    )
    return QapBenchmarkModel(
        program=builder.freeze(),
        assignment_node_id=assignment.node_id,
        default_assignment=default_assignment,
        instance=instance,
    )
