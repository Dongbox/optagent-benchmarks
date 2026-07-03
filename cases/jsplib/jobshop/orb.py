from __future__ import annotations

from benchmarks.cases.jsplib.jobshop._domain import (
    make_job_shop_case,
    RAW_DIR,
)

CASE_MODULE = __name__

ORB03 = make_job_shop_case(
    benchmark_id='jsplib_orb03',
    instance='orb03',
    tier='calibration',
    jobs=10,
    machines=10,
    raw_path=RAW_DIR / 'orb03.json',
    objective=1005,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/orb03.json',
    reported_time_seconds=1,
)

ORB04 = make_job_shop_case(
    benchmark_id='jsplib_orb04',
    instance='orb04',
    tier='calibration',
    jobs=10,
    machines=10,
    raw_path=RAW_DIR / 'orb04.json',
    objective=1005,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/orb04.json',
    reported_time_seconds=1,
)

CASES = (ORB03, ORB04)
