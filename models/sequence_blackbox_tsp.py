from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from optagent import ExternalCallbackContext, ModelBuilder

from benchmarks.loaders.sequence_blackbox_tsp import TspInstance


@dataclass(frozen=True)
class TspBenchmarkModel:
    program: Any
    sequence_node_id: int
    default_tour: list[int]
    instance: TspInstance


def build_tsp_model(case: dict[str, Any], instance: TspInstance) -> TspBenchmarkModel:
    default_tour = list(range(instance.dimension))
    builder = ModelBuilder(
        metadata={
            "benchmark_id": case["benchmark_id"],
            "family": "sequence_blackbox_tsp",
            "model_style": "sequence_var_external_call",
            "source": "TSPLIB95",
            "dimension": instance.dimension,
            "edge_weight_type": instance.edge_weight_type,
        }
    )
    tour = builder.sequence_var(size=instance.dimension, default=default_tour, name="tour")

    def tour_length(ctx: ExternalCallbackContext) -> int:
        order = [int(item) for item in ctx.value(tour)]
        return instance.tour_length(order, include_return_edge=True)

    builder.minimize(
        builder.external_call(
            tour_length,
            name="tour_length",
            pure=True,
            deterministic=True,
            cacheable=True,
            timeout_ms=100,
            depends_on=(tour,),
        ),
        name="tour_length",
    )
    return TspBenchmarkModel(
        program=builder.freeze(),
        sequence_node_id=tour.node_id,
        default_tour=default_tour,
        instance=instance,
    )
