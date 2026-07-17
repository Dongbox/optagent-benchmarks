from __future__ import annotations

from benchmarks.cases.psplib.rcpsp._domain import RAW_DIR, make_rcpsp_case

CASE_MODULE = __name__

_CASE_DATA = (
    ('13_1', 104, 112, False),
    ('16_1', 64, 64, True),
    ('16_3', 53, 53, True),
    ('21_2', 108, 108, True),
    ('23_7', 60, 60, True),
    ('25_2', 98, 98, True),
    ('27_2', 74, 74, True),
    ('29_6', 145, 154, False),
    ('2_3', 78, 78, True),
    ('33_5', 108, 108, True),
    ('33_8', 79, 79, True),
    ('34_4', 83, 83, True),
    ('3_3', 105, 105, True),
    ('41_6', 134, 134, True),
    ('45_2', None, 144, False),
    ('45_4', None, 108, False),
    ('48_1', None, 71, False),
    ('48_3', None, 84, False),
    ('5_1', 76, 76, True),
    ('9_6', 105, 111, False),
)

CASES = tuple(
    make_rcpsp_case(
        benchmark_id=f"psplib_j60_{suffix}",
        instance=f"j60_{suffix}",
        tier="calibration",
        activities=60,
        renewable_resources=4,
        raw_path=RAW_DIR / f"j60_{suffix}.rcp",
        objective=upper_bound,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        is_optimal=is_optimal,
        case_module=CASE_MODULE,
        instance_url=f"https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/rcpsp/instances/j60/j60_{suffix}.rcp",
    )
    for suffix, lower_bound, upper_bound, is_optimal in _CASE_DATA
)
