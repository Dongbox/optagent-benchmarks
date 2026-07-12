from __future__ import annotations

from benchmarks.cases.jsplib.jobshop._domain import (
    make_job_shop_case,
    RAW_DIR,
)

CASE_MODULE = __name__

YN1 = make_job_shop_case(
    benchmark_id='jsplib_yn1',
    instance='yn1',
    tier='full',
    jobs=20,
    machines=20,
    raw_path=RAW_DIR / 'yn1.json',
    objective=884,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/yn1.json',
    reported_time_seconds=360,
)

CASES = (YN1,)
