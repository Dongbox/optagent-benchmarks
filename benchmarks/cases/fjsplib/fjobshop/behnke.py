from __future__ import annotations

from benchmarks.cases.fjsplib.fjobshop._domain import (
    make_flexible_job_shop_case,
    RAW_DIR,
)

CASE_MODULE = __name__

LAR01_3 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_lar01_3',
    instance='lar01_3',
    tier='pressure',
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

MED01_4 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_med01_4',
    instance='med01_4',
    tier='pressure',
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

SM01_1 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_sm01_1',
    instance='sm01_1',
    tier='full',
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

SM02_5 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_sm02_5',
    instance='sm02_5',
    tier='pressure',
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

CASES = (
    LAR01_3,
    MED01_4,
    SM01_1,
    SM02_5,
)
