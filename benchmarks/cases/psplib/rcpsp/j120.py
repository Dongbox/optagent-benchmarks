from __future__ import annotations

from benchmarks.cases.psplib.rcpsp._domain import RAW_DIR, make_rcpsp_case

CASE_MODULE = __name__

_CASE_DATA = (
    ('16_3', 219, 233, False),
    ('1_3', 125, 125, True),
    ('20_9', None, 80, False),
    ('27_5', None, 111, False),
    ('44_10', None, 98, False),
    ('49_5', None, 89, False),
    ('56_4', None, 221, False),
    ('56_9', None, 287, False),
    ('58_8', None, 132, False),
    ('5_3', 72, 72, True),
)

CASES = tuple(
    make_rcpsp_case(
        benchmark_id=f"psplib_j120_{suffix}",
        instance=f"j120_{suffix}",
        tier="pressure",
        activities=120,
        renewable_resources=4,
        raw_path=RAW_DIR / f"j120_{suffix}.rcp",
        objective=upper_bound,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        is_optimal=is_optimal,
        case_module=CASE_MODULE,
        instance_url=f"https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/rcpsp/instances/j120/j120_{suffix}.rcp",
    )
    for suffix, lower_bound, upper_bound, is_optimal in _CASE_DATA
)
