from __future__ import annotations

from benchmarks.cases.jsplib.jobshop._domain import (
    make_job_shop_case,
    RAW_DIR,
)

CASE_MODULE = __name__

SWV01 = make_job_shop_case(
    benchmark_id='jsplib_swv01',
    instance='swv01',
    tier='full',
    jobs=20,
    machines=10,
    raw_path=RAW_DIR / 'swv01.json',
    objective=1407,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/swv01.json',
    reported_time_seconds=1,
)

CASES = (SWV01,)
