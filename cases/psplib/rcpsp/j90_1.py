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

J90_1_1 = make_rcpsp_case(
    benchmark_id='psplib_j90_1_1',
    instance='j90_1_1',
    tier='calibration',
    activities=90,
    renewable_resources=4,
    raw_path=RAW_DIR / 'j90_1_1.rcp',
    objective=73,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/rcpsp/instances/j90/j90_1_1.rcp',
)

J90_1_8 = make_rcpsp_case(
    benchmark_id='psplib_j90_1_8',
    instance='j90_1_8',
    tier='calibration',
    activities=90,
    renewable_resources=4,
    raw_path=RAW_DIR / 'j90_1_8.rcp',
    objective=95,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/rcpsp/instances/j90/j90_1_8.rcp',
)

CASES = (J90_1_1, J90_1_8)
