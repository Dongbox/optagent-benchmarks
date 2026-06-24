from __future__ import annotations

from benchmarks.cases.jsplib.jobshop._domain import (
    make_job_shop_case,
    RAW_DIR,
)

CASE_MODULE = __name__

FT06 = make_job_shop_case(
    benchmark_id='jsplib_ft06',
    instance='ft06',
    tier='smoke',
    jobs=6,
    machines=6,
    raw_path=RAW_DIR / 'ft06.json',
    objective=55,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/ft06.json',
    reported_time_seconds=1,
)

FT10 = make_job_shop_case(
    benchmark_id='jsplib_ft10',
    instance='ft10',
    tier='smoke',
    jobs=10,
    machines=10,
    raw_path=RAW_DIR / 'ft10.json',
    objective=930,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/ft10.json',
    reported_time_seconds=1,
)

CASES = (FT06, FT10)
