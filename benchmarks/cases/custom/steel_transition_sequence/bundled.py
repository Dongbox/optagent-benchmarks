from __future__ import annotations

from benchmarks.cases.custom.steel_transition_sequence._domain import make_steel_case

CASE_MODULE = __name__

BUNDLED_HEAD40 = make_steel_case(
    instance="bundled_head40",
    tier="calibration",
    coils=40,
    reference={
        "objective": 22,
        "status": "baseline",
        "value_kind": "baseline",
        "notes": "Baseline is the natural bundled data order from the steel example.",
    },
    case_module=CASE_MODULE,
)

BUNDLED = make_steel_case(
    instance="bundled",
    tier="full",
    coils=285,
    reference={
        "objective": 1,
        "status": "baseline",
        "value_kind": "baseline",
        "notes": "Baseline is the natural bundled data order from the steel example.",
    },
    case_module=CASE_MODULE,
)

CASES = (
    BUNDLED_HEAD40,
    BUNDLED,
)
