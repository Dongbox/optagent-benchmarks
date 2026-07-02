from __future__ import annotations

from benchmarks.cases.jsplib.jobshop._domain import (
    make_job_shop_case,
    RAW_DIR,
)

CASE_MODULE = __name__

ABZ5 = make_job_shop_case(
    benchmark_id='jsplib_abz5',
    instance='abz5',
    tier='calibration',
    jobs=10,
    machines=10,
    raw_path=RAW_DIR / 'abz5.json',
    objective=1234,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/abz5.json',
    reported_time_seconds=1,
)

ABZ6 = make_job_shop_case(
    benchmark_id='jsplib_abz6',
    instance='abz6',
    tier='calibration',
    jobs=10,
    machines=10,
    raw_path=RAW_DIR / 'abz6.json',
    objective=943,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/abz6.json',
    reported_time_seconds=1,
)

ABZ7 = make_job_shop_case(
    benchmark_id='jsplib_abz7',
    instance='abz7',
    tier='full',
    jobs=20,
    machines=15,
    raw_path=RAW_DIR / 'abz7.json',
    objective=656,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/abz7.json',
    reported_time_seconds=10,
)

CASES = (ABZ5, ABZ6, ABZ7)
