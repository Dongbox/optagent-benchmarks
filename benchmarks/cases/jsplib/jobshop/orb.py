from __future__ import annotations

from benchmarks.cases.jsplib.jobshop._domain import (
    RAW_DIR,
    make_job_shop_case,
)

CASE_MODULE = __name__

ORB01 = make_job_shop_case(
    benchmark_id='jsplib_orb01',
    instance='orb01',
    tier='calibration',
    jobs=10,
    machines=10,
    raw_path=RAW_DIR / 'orb01.json',
    objective=1059,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/orb01.json',
    reported_time_seconds=1,
)

ORB02 = make_job_shop_case(
    benchmark_id='jsplib_orb02',
    instance='orb02',
    tier='calibration',
    jobs=10,
    machines=10,
    raw_path=RAW_DIR / 'orb02.json',
    objective=888,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/orb02.json',
    reported_time_seconds=1,
)

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

ORB05 = make_job_shop_case(
    benchmark_id='jsplib_orb05',
    instance='orb05',
    tier='calibration',
    jobs=10,
    machines=10,
    raw_path=RAW_DIR / 'orb05.json',
    objective=887,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/orb05.json',
    reported_time_seconds=1,
)

ORB07 = make_job_shop_case(
    benchmark_id='jsplib_orb07',
    instance='orb07',
    tier='smoke',
    jobs=10,
    machines=10,
    raw_path=RAW_DIR / 'orb07.json',
    objective=397,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/orb07.json',
    reported_time_seconds=1,
)

ORB08 = make_job_shop_case(
    benchmark_id='jsplib_orb08',
    instance='orb08',
    tier='smoke',
    jobs=10,
    machines=10,
    raw_path=RAW_DIR / 'orb08.json',
    objective=899,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/orb08.json',
    reported_time_seconds=1,
)

ORB09 = make_job_shop_case(
    benchmark_id='jsplib_orb09',
    instance='orb09',
    tier='calibration',
    jobs=10,
    machines=10,
    raw_path=RAW_DIR / 'orb09.json',
    objective=934,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/orb09.json',
    reported_time_seconds=1,
)

ORB10 = make_job_shop_case(
    benchmark_id='jsplib_orb10',
    instance='orb10',
    tier='smoke',
    jobs=10,
    machines=10,
    raw_path=RAW_DIR / 'orb10.json',
    objective=944,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/orb10.json',
    reported_time_seconds=1,
)

CASES = (
    ORB01,
    ORB02,
    ORB03,
    ORB04,
    ORB05,
    ORB07,
    ORB08,
    ORB09,
    ORB10,
)
