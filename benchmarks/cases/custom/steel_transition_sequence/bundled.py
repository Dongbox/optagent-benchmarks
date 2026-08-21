from __future__ import annotations

from benchmarks.cases.custom.steel_transition_sequence._domain import make_steel_case

CASE_MODULE = __name__

BUNDLED_HEAD40 = make_steel_case(
    instance="bundled_head40",
    tier="calibration",
    coils=40,
    reference={
        "objective": 3,
        "status": "optimal",
        "value_kind": "optimal",
        "notes": "CP-SAT proved optimum via augmented Hamiltonian-cycle feasibility checks.",
    },
    case_module=CASE_MODULE,
)

BUNDLED = make_steel_case(
    instance="bundled",
    tier="full",
    coils=285,
    reference={
        "objective": 1,
        "status": "optimal",
        "value_kind": "optimal",
        "notes": "CP-SAT proved optimum via augmented Hamiltonian-cycle feasibility checks.",
    },
    case_module=CASE_MODULE,
)

CASES = (
    BUNDLED_HEAD40,
    BUNDLED,
)
