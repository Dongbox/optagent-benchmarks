from __future__ import annotations

from typing import Any

from optagent import ModelBuilder

from benchmarks.loaders.sequence_blackbox_tsp import TspInstance
from benchmarks.models.sequence_blackbox_tsp import TspBenchmarkModel


GRAPH_TSP_MODEL_STYLE = "sequence_var_sequence_transition_sum"


def build_tsp_graph_model(case: dict[str, Any], instance: TspInstance) -> TspBenchmarkModel:
    default_tour = list(range(instance.dimension))
    distance_matrix = [
        [instance.distance(left, right) for right in range(instance.dimension)]
        for left in range(instance.dimension)
    ]
    builder = ModelBuilder(
        metadata={
            "benchmark_id": case["benchmark_id"],
            "family": "sequence_blackbox_tsp",
            "model_style": GRAPH_TSP_MODEL_STYLE,
            "source": "TSPLIB95",
            "dimension": instance.dimension,
            "edge_weight_type": instance.edge_weight_type,
            "sequence_graph_symmetric": _is_symmetric(distance_matrix),
            "sequence_graph_weight_format": "dense_matrix",
        }
    )
    tour = builder.sequence_var(size=instance.dimension, default=default_tour, name="tour")
    builder.minimize(
        builder.sequence_transition_sum(
            tour,
            distance_matrix,
            include_return_edge=True,
            cost_semantics="distance",
        ),
        name="tour_length",
    )
    return TspBenchmarkModel(
        program=builder.freeze(),
        sequence_node_id=tour.node_id,
        default_tour=default_tour,
        instance=instance,
    )


def _is_symmetric(matrix: list[list[int]]) -> bool:
    for left, row in enumerate(matrix):
        for right, value in enumerate(row):
            if matrix[right][left] != value:
                return False
    return True
