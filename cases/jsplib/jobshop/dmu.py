from __future__ import annotations

from benchmarks.cases.jsplib.jobshop._domain import (
    make_job_shop_case,
    RAW_DIR,
)

CASE_MODULE = __name__

DMU01 = make_job_shop_case(
    benchmark_id='jsplib_dmu01',
    instance='dmu01',
    tier='full',
    jobs=20,
    machines=15,
    raw_path=RAW_DIR / 'dmu01.json',
    objective=2563,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/dmu01.json',
    reported_time_seconds=60,
)

CASES = (DMU01,)
