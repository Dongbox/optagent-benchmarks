from __future__ import annotations

from benchmarks.cases.psplib.rcpsp._common import (
    make_rcpsp_case,
    RAW_DIR,
    SOURCE,
    SOURCE_KEY,
    PROBLEM_TYPE,
    INSTANCE_TYPE,
    FAMILY,
    MODEL_STYLE,
)

CASE_MODULE = __name__

J90_5_3 = make_rcpsp_case(
    benchmark_id='psplib_j90_5_3',
    instance='j90_5_3',
    tier='full',
    activities=90,
    renewable_resources=4,
    raw_path=RAW_DIR / 'j90_5_3.rcp',
    objective=87,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/rcpsp/instances/j90/j90_5_3.rcp',
)

CASES = (J90_5_3,)
