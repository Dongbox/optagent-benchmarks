from __future__ import annotations

from benchmarks.cases.jsplib.jobshop._domain import (
    make_job_shop_case,
    RAW_DIR,
)

CASE_MODULE = __name__

LA01 = make_job_shop_case(
    benchmark_id='jsplib_la01',
    instance='la01',
    tier='smoke',
    jobs=10,
    machines=5,
    raw_path=RAW_DIR / 'la01.json',
    objective=666,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/la01.json',
    reported_time_seconds=1,
)

LA16 = make_job_shop_case(
    benchmark_id='jsplib_la16',
    instance='la16',
    tier='calibration',
    jobs=10,
    machines=10,
    raw_path=RAW_DIR / 'la16.json',
    objective=945,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/la16.json',
    reported_time_seconds=1,
)

LA21 = make_job_shop_case(
    benchmark_id='jsplib_la21',
    instance='la21',
    tier='calibration',
    jobs=15,
    machines=10,
    raw_path=RAW_DIR / 'la21.json',
    objective=1046,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/la21.json',
    reported_time_seconds=1,
)

LA31 = make_job_shop_case(
    benchmark_id='jsplib_la31',
    instance='la31',
    tier='full',
    jobs=30,
    machines=10,
    raw_path=RAW_DIR / 'la31.json',
    objective=1784,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/la31.json',
    reported_time_seconds=1,
)

LA36 = make_job_shop_case(
    benchmark_id='jsplib_la36',
    instance='la36',
    tier='full',
    jobs=15,
    machines=15,
    raw_path=RAW_DIR / 'la36.json',
    objective=1268,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/la36.json',
    reported_time_seconds=1,
)

CASES = (LA01, LA16, LA21, LA31, LA36)
