from __future__ import annotations

from benchmarks.cases.fjsplib.fjobshop._domain import (
    make_flexible_job_shop_case,
    RAW_DIR,
)

CASE_MODULE = __name__

SM01_1 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_sm01_1',
    instance='sm01_1',
    tier='calibration',
    jobs=10,
    machines=20,
    operations=50,
    candidates=304,
    raw_path=RAW_DIR / 'sm01_1.json',
    objective=91,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 91,
        'lower_bound': 70,
        'upper_bound': 91,
    },
)

MED01_4 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_med01_4',
    instance='med01_4',
    tier='calibration',
    jobs=10,
    machines=40,
    operations=50,
    candidates=564,
    raw_path=RAW_DIR / 'med01_4.json',
    objective=87,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 87,
        'lower_bound': 70,
        'upper_bound': 87,
    },
)

SM02_5 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_sm02_5',
    instance='sm02_5',
    tier='calibration',
    jobs=20,
    machines=20,
    operations=100,
    candidates=612,
    raw_path=RAW_DIR / 'sm02_5.json',
    objective=133,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 133,
        'lower_bound': 81,
        'upper_bound': 133,
    },
)

LAR01_3 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_lar01_3',
    instance='lar01_3',
    tier='full',
    jobs=10,
    machines=60,
    operations=50,
    candidates=964,
    raw_path=RAW_DIR / 'lar01_3.json',
    objective=86,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 86,
        'lower_bound': 68,
        'upper_bound': 86,
    },
)

MED02_2 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_med02_2',
    instance='med02_2',
    tier='full',
    jobs=20,
    machines=40,
    operations=100,
    candidates=1192,
    raw_path=RAW_DIR / 'med02_2.json',
    objective=132,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 132,
        'lower_bound': 81,
        'upper_bound': 132,
    },
)

SM03_4 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_sm03_4',
    instance='sm03_4',
    tier='full',
    jobs=50,
    machines=20,
    operations=250,
    candidates=1524,
    raw_path=RAW_DIR / 'sm03_4.json',
    objective=258,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 258,
        'lower_bound': 164,
        'upper_bound': 258,
    },
)

MED03_2 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_med03_2',
    instance='med03_2',
    tier='pressure',
    jobs=50,
    machines=40,
    operations=250,
    candidates=3052,
    raw_path=RAW_DIR / 'med03_2.json',
    objective=259,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 259,
        'lower_bound': 77,
        'upper_bound': 259,
    },
)

SM04_3 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_sm04_3',
    instance='sm04_3',
    tier='pressure',
    jobs=100,
    machines=20,
    operations=500,
    candidates=3164,
    raw_path=RAW_DIR / 'sm04_3.json',
    objective=555,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 555,
        'lower_bound': 321,
        'upper_bound': 555,
    },
)

CASES = (
    SM01_1,
    MED01_4,
    SM02_5,
    LAR01_3,
    MED02_2,
    SM03_4,
    MED03_2,
    SM04_3,
)
