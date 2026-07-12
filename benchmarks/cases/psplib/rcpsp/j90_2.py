from __future__ import annotations

from benchmarks.cases.psplib.rcpsp._domain import (
    make_rcpsp_case,
    RAW_DIR,
)

CASE_MODULE = __name__

J90_2_4 = make_rcpsp_case(
    benchmark_id='psplib_j90_2_4',
    instance='j90_2_4',
    tier='calibration',
    activities=90,
    renewable_resources=4,
    raw_path=RAW_DIR / 'j90_2_4.rcp',
    objective=70,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/rcpsp/instances/j90/j90_2_4.rcp',
)

CASES = (J90_2_4,)
