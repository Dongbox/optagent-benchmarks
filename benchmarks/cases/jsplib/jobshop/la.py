from __future__ import annotations

from benchmarks.cases.jsplib.jobshop._domain import (
    RAW_DIR,
    make_job_shop_case,
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

LA02 = make_job_shop_case(
    benchmark_id='jsplib_la02',
    instance='la02',
    tier='smoke',
    jobs=10,
    machines=5,
    raw_path=RAW_DIR / 'la02.json',
    objective=655,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/la02.json',
    reported_time_seconds=1,
)

LA03 = make_job_shop_case(
    benchmark_id='jsplib_la03',
    instance='la03',
    tier='smoke',
    jobs=10,
    machines=5,
    raw_path=RAW_DIR / 'la03.json',
    objective=597,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/la03.json',
    reported_time_seconds=1,
)

LA04 = make_job_shop_case(
    benchmark_id='jsplib_la04',
    instance='la04',
    tier='smoke',
    jobs=10,
    machines=5,
    raw_path=RAW_DIR / 'la04.json',
    objective=590,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/la04.json',
    reported_time_seconds=1,
)

LA05 = make_job_shop_case(
    benchmark_id='jsplib_la05',
    instance='la05',
    tier='smoke',
    jobs=10,
    machines=5,
    raw_path=RAW_DIR / 'la05.json',
    objective=593,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/la05.json',
    reported_time_seconds=1,
)

LA09 = make_job_shop_case(
    benchmark_id='jsplib_la09',
    instance='la09',
    tier='smoke',
    jobs=15,
    machines=5,
    raw_path=RAW_DIR / 'la09.json',
    objective=951,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/la09.json',
    reported_time_seconds=1,
)

LA11 = make_job_shop_case(
    benchmark_id='jsplib_la11',
    instance='la11',
    tier='smoke',
    jobs=20,
    machines=5,
    raw_path=RAW_DIR / 'la11.json',
    objective=1222,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/la11.json',
    reported_time_seconds=1,
)

LA12 = make_job_shop_case(
    benchmark_id='jsplib_la12',
    instance='la12',
    tier='smoke',
    jobs=20,
    machines=5,
    raw_path=RAW_DIR / 'la12.json',
    objective=1039,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/la12.json',
    reported_time_seconds=1,
)

LA13 = make_job_shop_case(
    benchmark_id='jsplib_la13',
    instance='la13',
    tier='calibration',
    jobs=20,
    machines=5,
    raw_path=RAW_DIR / 'la13.json',
    objective=1150,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/la13.json',
    reported_time_seconds=1,
)

LA14 = make_job_shop_case(
    benchmark_id='jsplib_la14',
    instance='la14',
    tier='smoke',
    jobs=20,
    machines=5,
    raw_path=RAW_DIR / 'la14.json',
    objective=1292,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/la14.json',
    reported_time_seconds=1,
)

LA15 = make_job_shop_case(
    benchmark_id='jsplib_la15',
    instance='la15',
    tier='calibration',
    jobs=20,
    machines=5,
    raw_path=RAW_DIR / 'la15.json',
    objective=1207,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/la15.json',
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

LA17 = make_job_shop_case(
    benchmark_id='jsplib_la17',
    instance='la17',
    tier='smoke',
    jobs=10,
    machines=10,
    raw_path=RAW_DIR / 'la17.json',
    objective=784,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/la17.json',
    reported_time_seconds=1,
)

LA19 = make_job_shop_case(
    benchmark_id='jsplib_la19',
    instance='la19',
    tier='calibration',
    jobs=10,
    machines=10,
    raw_path=RAW_DIR / 'la19.json',
    objective=842,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/la19.json',
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

LA22 = make_job_shop_case(
    benchmark_id='jsplib_la22',
    instance='la22',
    tier='calibration',
    jobs=15,
    machines=10,
    raw_path=RAW_DIR / 'la22.json',
    objective=927,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/la22.json',
    reported_time_seconds=1,
)

LA23 = make_job_shop_case(
    benchmark_id='jsplib_la23',
    instance='la23',
    tier='calibration',
    jobs=15,
    machines=10,
    raw_path=RAW_DIR / 'la23.json',
    objective=1032,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/la23.json',
    reported_time_seconds=1,
)

LA25 = make_job_shop_case(
    benchmark_id='jsplib_la25',
    instance='la25',
    tier='calibration',
    jobs=15,
    machines=10,
    raw_path=RAW_DIR / 'la25.json',
    objective=977,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/la25.json',
    reported_time_seconds=1,
)

LA30 = make_job_shop_case(
    benchmark_id='jsplib_la30',
    instance='la30',
    tier='full',
    jobs=20,
    machines=10,
    raw_path=RAW_DIR / 'la30.json',
    objective=1355,
    case_module=CASE_MODULE,
    instance_url='https://raw.githubusercontent.com/ScheduleOpt/benchmarks/main/jobshop/instances/json/la30.json',
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

CASES = (
    LA01,
    LA02,
    LA03,
    LA04,
    LA05,
    LA09,
    LA11,
    LA12,
    LA13,
    LA14,
    LA15,
    LA16,
    LA17,
    LA19,
    LA21,
    LA22,
    LA23,
    LA25,
    LA30,
    LA36,
    LA31,
)
