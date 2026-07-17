from __future__ import annotations

from benchmarks.cases.psplib.rcpsp._domain import RAW_DIR, make_rcpsp_case

CASE_MODULE = __name__

_CASE_DATA = (
    ('11_9', 67, 67, True),
    ('13_8', 106, 106, True),
    ('15_5', 58, 58, True),
    ('19_3', 83, 83, True),
    ('1_4', 62, 62, True),
    ('1_5', 39, 39, True),
    ('1_6', 48, 48, True),
    ('21_9', 69, 69, True),
    ('27_1', 43, 43, True),
    ('34_3', 69, 69, True),
    ('37_3', 81, 81, True),
    ('40_10', 51, 51, True),
    ('41_5', 99, 99, True),
    ('45_7', 101, 101, True),
    ('45_8', 94, 94, True),
    ('4_6', 45, 45, True),
    ('7_1', 55, 55, True),
    ('8_10', 67, 67, True),
    ('9_1', 83, 83, True),
    ('9_9', 63, 63, True),
)

CASES = tuple(
    make_rcpsp_case(
        benchmark_id=f"psplib_j30_{suffix}",
        instance=f"j30_{suffix}",
        tier="smoke",
        activities=30,
        renewable_resources=4,
        raw_path=RAW_DIR / f"j30_{suffix}.rcp",
        objective=upper_bound,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        is_optimal=is_optimal,
        case_module=CASE_MODULE,
        instance_url=f"https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/rcpsp/instances/j30/j30_{suffix}.rcp",
    )
    for suffix, lower_bound, upper_bound, is_optimal in _CASE_DATA
)
