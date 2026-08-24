from __future__ import annotations

from benchmarks.cases.custom.steel_transition_sequence._domain import make_steel_case

CASE_MODULE = __name__

TOY = make_steel_case(
    instance="toy",
    tier="smoke",
    coils=5,
    reference={
        "objective": 3,
        "status": "optimal",
        "value_kind": "optimal",
        "notes": "The five-coil toy instance is small enough to verify by exhaustive permutation.",
    },
    case_module=CASE_MODULE,
)

CASES = (TOY,)
