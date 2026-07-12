from __future__ import annotations

from benchmarks.cases.jsplib.jobshop._domain import (
    make_job_shop_case,
    RAW_DIR,
)

CASE_MODULE = __name__

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

CASES = (TA11JS, TA21JS, TA31JS, TA41JS, TA51JS)
