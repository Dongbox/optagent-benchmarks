from __future__ import annotations

from benchmarks.cases.psplib.rcpsp._domain import RAW_DIR, make_rcpsp_case

CASE_MODULE = __name__

_CASE_DATA = (
    ('13_2', 118, 127, False),
    ('16_7', 65, 65, True),
    ('17_10', 89, 89, True),
    ('19_5', 66, 66, True),
    ('1_8', 95, 95, True),
    ('29_1', 125, 135, False),
    ('32_9', 95, 95, True),
    ('33_1', 99, 99, True),
    ('35_6', 72, 72, True),
    ('36_9', 102, 102, True),
    ('41_9', 109, 118, False),
    ('45_5', 164, 173, False),
    ('47_10', None, 65, False),
    ('47_5', None, 93, False),
    ('6_7', 71, 71, True),
)

CASES = tuple(
    make_rcpsp_case(
        benchmark_id=f"psplib_j90_{suffix}",
        instance=f"j90_{suffix}",
        tier="full",
        activities=90,
        renewable_resources=4,
        raw_path=RAW_DIR / f"j90_{suffix}.rcp",
        objective=upper_bound,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        is_optimal=is_optimal,
        case_module=CASE_MODULE,
        instance_url=f"https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/rcpsp/instances/j90/j90_{suffix}.rcp",
    )
    for suffix, lower_bound, upper_bound, is_optimal in _CASE_DATA
)
