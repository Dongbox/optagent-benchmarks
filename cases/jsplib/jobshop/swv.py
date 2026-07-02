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

SWV06 = make_job_shop_case(
    benchmark_id='jsplib_swv06',
    instance='swv06',
    tier='full',
    jobs=20,
    machines=15,
    raw_path=RAW_DIR / 'swv06.json',
    objective=1667,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/swv06.json',
    reported_time_seconds=2400,
)

SWV11 = make_job_shop_case(
    benchmark_id='jsplib_swv11',
    instance='swv11',
    tier='pressure',
    jobs=50,
    machines=10,
    raw_path=RAW_DIR / 'swv11.json',
    objective=2983,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/swv11.json',
    reported_time_seconds=60,
)

SWV16 = make_job_shop_case(
    benchmark_id='jsplib_swv16',
    instance='swv16',
    tier='pressure',
    jobs=50,
    machines=10,
    raw_path=RAW_DIR / 'swv16.json',
    objective=2924,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/swv16.json',
    reported_time_seconds=1,
)

CASES = (SWV01, SWV06, SWV11, SWV16)
