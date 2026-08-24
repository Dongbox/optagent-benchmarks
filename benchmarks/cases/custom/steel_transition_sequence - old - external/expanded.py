from __future__ import annotations

from benchmarks.cases.custom.steel_transition_sequence._domain import make_steel_case

CASE_MODULE = __name__

SAMPLE303 = make_steel_case(
    instance="sample303",
    tier="full",
    coils=303,
    reference={
        "objective": 1,
        "status": "optimal",
        "value_kind": "optimal",
        "notes": "CP-SAT proved optimum via augmented Hamiltonian-cycle feasibility checks.",
    },
    case_module=CASE_MODULE,
)

_GRAPH900_OBJECTIVES = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
_GRAPH1000_OBJECTIVES = (1, 0, 0, 0, 0, 0, 0, 1, 0, 0)


def _graph_case(*, nodes: int, graph_id: int, objective: int):
    return make_steel_case(
        instance=f"graph{nodes}_{graph_id:02d}",
        tier="pressure",
        coils=nodes,
        reference={
            "objective": objective,
            "status": "optimal",
            "value_kind": "optimal",
            "notes": (
                f"CP-SAT optimal transition count from "
                f"cp_sat_optimal_results_{nodes}.csv, graph_id={graph_id}."
            ),
        },
        case_module=CASE_MODULE,
    )


GRAPH900_CASES = tuple(
    _graph_case(nodes=900, graph_id=graph_id, objective=objective)
    for graph_id, objective in enumerate(_GRAPH900_OBJECTIVES)
)
GRAPH1000_CASES = tuple(
    _graph_case(nodes=1000, graph_id=graph_id, objective=objective)
    for graph_id, objective in enumerate(_GRAPH1000_OBJECTIVES)
)

CASES = (
    SAMPLE303,
    *GRAPH900_CASES,
    *GRAPH1000_CASES,
)
