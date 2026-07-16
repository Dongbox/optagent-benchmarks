from __future__ import annotations

from benchmarks.cases.jsplib.jobshop._domain import (
    RAW_DIR,
    make_job_shop_case,
)

CASE_MODULE = __name__

TAI_10_10_1 = make_job_shop_case(
    benchmark_id='jsplib_tai_10_10_1',
    instance='tai_10_10_1',
    tier='smoke',
    jobs=10,
    machines=10,
    raw_path=RAW_DIR / 'tai_10_10_1.json',
    objective=8219,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/tai_10_10_1.json',
    reported_time_seconds=1,
)

TAI_10_10_10 = make_job_shop_case(
    benchmark_id='jsplib_tai_10_10_10',
    instance='tai_10_10_10',
    tier='calibration',
    jobs=10,
    machines=10,
    raw_path=RAW_DIR / 'tai_10_10_10.json',
    objective=8481,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/tai_10_10_10.json',
    reported_time_seconds=1,
)

TAI_10_10_2 = make_job_shop_case(
    benchmark_id='jsplib_tai_10_10_2',
    instance='tai_10_10_2',
    tier='smoke',
    jobs=10,
    machines=10,
    raw_path=RAW_DIR / 'tai_10_10_2.json',
    objective=7416,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/tai_10_10_2.json',
    reported_time_seconds=1,
)

TAI_10_10_3 = make_job_shop_case(
    benchmark_id='jsplib_tai_10_10_3',
    instance='tai_10_10_3',
    tier='calibration',
    jobs=10,
    machines=10,
    raw_path=RAW_DIR / 'tai_10_10_3.json',
    objective=8094,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/tai_10_10_3.json',
    reported_time_seconds=1,
)

TAI_10_10_4 = make_job_shop_case(
    benchmark_id='jsplib_tai_10_10_4',
    instance='tai_10_10_4',
    tier='smoke',
    jobs=10,
    machines=10,
    raw_path=RAW_DIR / 'tai_10_10_4.json',
    objective=8657,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/tai_10_10_4.json',
    reported_time_seconds=1,
)

TAI_10_10_5 = make_job_shop_case(
    benchmark_id='jsplib_tai_10_10_5',
    instance='tai_10_10_5',
    tier='smoke',
    jobs=10,
    machines=10,
    raw_path=RAW_DIR / 'tai_10_10_5.json',
    objective=7936,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/tai_10_10_5.json',
    reported_time_seconds=1,
)

TAI_10_10_6 = make_job_shop_case(
    benchmark_id='jsplib_tai_10_10_6',
    instance='tai_10_10_6',
    tier='calibration',
    jobs=10,
    machines=10,
    raw_path=RAW_DIR / 'tai_10_10_6.json',
    objective=8509,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/tai_10_10_6.json',
    reported_time_seconds=1,
)

TAI_10_10_8 = make_job_shop_case(
    benchmark_id='jsplib_tai_10_10_8',
    instance='tai_10_10_8',
    tier='calibration',
    jobs=10,
    machines=10,
    raw_path=RAW_DIR / 'tai_10_10_8.json',
    objective=7788,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/tai_10_10_8.json',
    reported_time_seconds=1,
)

TA11JS = make_job_shop_case(
    benchmark_id='jsplib_ta11js',
    instance='ta11js',
    tier='full',
    jobs=20,
    machines=15,
    raw_path=RAW_DIR / 'ta11js.json',
    objective=1357,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/ta11js.json',
    reported_time_seconds=60,
)

TA21JS = make_job_shop_case(
    benchmark_id='jsplib_ta21js',
    instance='ta21js',
    tier='full',
    jobs=20,
    machines=20,
    raw_path=RAW_DIR / 'ta21js.json',
    objective=1642,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/ta21js.json',
    reported_time_seconds=60,
)

TA31JS = make_job_shop_case(
    benchmark_id='jsplib_ta31js',
    instance='ta31js',
    tier='full',
    jobs=30,
    machines=15,
    raw_path=RAW_DIR / 'ta31js.json',
    objective=1764,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/ta31js.json',
    reported_time_seconds=10,
)

TA41JS = make_job_shop_case(
    benchmark_id='jsplib_ta41js',
    instance='ta41js',
    tier='pressure',
    jobs=30,
    machines=20,
    raw_path=RAW_DIR / 'ta41js.json',
    objective=2005,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/ta41js.json',
    reference={
        'lower_bound': 1926,
        'upper_bound': 2005,
        'status': 'open',
        'value_kind': 'best_known_upper_bound',
    },
)

TA51JS = make_job_shop_case(
    benchmark_id='jsplib_ta51js',
    instance='ta51js',
    tier='pressure',
    jobs=50,
    machines=15,
    raw_path=RAW_DIR / 'ta51js.json',
    objective=2760,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/ta51js.json',
    reported_time_seconds=1,
)

CASES = (
    TAI_10_10_1,
    TAI_10_10_10,
    TAI_10_10_2,
    TAI_10_10_3,
    TAI_10_10_4,
    TAI_10_10_5,
    TAI_10_10_6,
    TAI_10_10_8,
    TA11JS,
    TA21JS,
    TA31JS,
    TA41JS,
    TA51JS,
)
