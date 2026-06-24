from __future__ import annotations

from benchmarks.cases.jsplib.jobshop._domain import (
    make_job_shop_case,
    RAW_DIR,
)

CASE_MODULE = __name__

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

CASES = (LA16, LA21)
