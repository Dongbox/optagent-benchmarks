from __future__ import annotations

from benchmarks.cases.jsplib.jobshop._domain import (
    RAW_DIR,
    make_job_shop_case,
)

CASE_MODULE = __name__

DMU01 = make_job_shop_case(
    benchmark_id='jsplib_dmu01',
    instance='dmu01',
    tier='full',
    jobs=20,
    machines=15,
    raw_path=RAW_DIR / 'dmu01.json',
    objective=2563,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/dmu01.json',
    reported_time_seconds=60,
)

DMU41 = make_job_shop_case(
    benchmark_id='jsplib_dmu41',
    instance='dmu41',
    tier='full',
    jobs=20,
    machines=15,
    raw_path=RAW_DIR / 'dmu41.json',
    objective=3248,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/dmu41.json',
    reference={
        'lower_bound': 3176,
        'upper_bound': 3248,
        'status': 'open',
        'value_kind': 'best_known_upper_bound',
    },
)

DMU46 = make_job_shop_case(
    benchmark_id='jsplib_dmu46',
    instance='dmu46',
    tier='full',
    jobs=20,
    machines=20,
    raw_path=RAW_DIR / 'dmu46.json',
    objective=4035,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/dmu46.json',
    reference={
        'lower_bound': 3780,
        'upper_bound': 4035,
        'status': 'open',
        'value_kind': 'best_known_upper_bound',
    },
)

DMU51 = make_job_shop_case(
    benchmark_id='jsplib_dmu51',
    instance='dmu51',
    tier='full',
    jobs=30,
    machines=15,
    raw_path=RAW_DIR / 'dmu51.json',
    objective=4151,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/dmu51.json',
    reference={
        'lower_bound': 4070,
        'upper_bound': 4151,
        'status': 'open',
        'value_kind': 'best_known_upper_bound',
    },
)

DMU56 = make_job_shop_case(
    benchmark_id='jsplib_dmu56',
    instance='dmu56',
    tier='pressure',
    jobs=30,
    machines=20,
    raw_path=RAW_DIR / 'dmu56.json',
    objective=4934,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/dmu56.json',
    reference={
        'lower_bound': 4755,
        'upper_bound': 4934,
        'status': 'open',
        'value_kind': 'best_known_upper_bound',
    },
)

DMU59 = make_job_shop_case(
    benchmark_id='jsplib_dmu59',
    instance='dmu59',
    tier='pressure',
    jobs=30,
    machines=20,
    raw_path=RAW_DIR / 'dmu59.json',
    objective=4607,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/dmu59.json',
    reference={
        'lower_bound': 4366,
        'upper_bound': 4607,
        'status': 'open',
        'value_kind': 'best_known_upper_bound',
    },
)

DMU32 = make_job_shop_case(
    benchmark_id='jsplib_dmu32',
    instance='dmu32',
    tier='pressure',
    jobs=50,
    machines=15,
    raw_path=RAW_DIR / 'dmu32.json',
    objective=5927,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/dmu32.json',
    reported_time_seconds=1,
)

DMU73 = make_job_shop_case(
    benchmark_id='jsplib_dmu73',
    instance='dmu73',
    tier='pressure',
    jobs=50,
    machines=15,
    raw_path=RAW_DIR / 'dmu73.json',
    objective=6132,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/dmu73.json',
    reference={
        'lower_bound': 6107,
        'upper_bound': 6132,
        'status': 'open',
        'value_kind': 'best_known_upper_bound',
    },
)

CASES = (
    DMU01,
    DMU41,
    DMU46,
    DMU51,
    DMU56,
    DMU59,
    DMU32,
    DMU73,
)
