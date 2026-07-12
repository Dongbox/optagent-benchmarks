from __future__ import annotations

from benchmarks.cases.fjsplib.fjobshop._domain import (
    make_flexible_job_shop_case,
    RAW_DIR,
)

CASE_MODULE = __name__

MT10C1 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_mt10c1',
    instance='mt10c1',
    tier='calibration',
    jobs=10,
    machines=11,
    operations=100,
    candidates=110,
    raw_path=RAW_DIR / 'mt10c1.json',
    objective=927,
    case_module=CASE_MODULE,
    reference={
        'kind': 'optimum',
        'objective': 927,
        'lower_bound': 927,
        'upper_bound': 927,
    },
)

MT10XXX = make_flexible_job_shop_case(
    benchmark_id='fjsplib_mt10xxx',
    instance='mt10xxx',
    tier='calibration',
    jobs=10,
    machines=13,
    operations=100,
    candidates=130,
    raw_path=RAW_DIR / 'mt10xxx.json',
    objective=918,
    case_module=CASE_MODULE,
    reference={
        'kind': 'optimum',
        'objective': 918,
        'lower_bound': 918,
        'upper_bound': 918,
    },
)

SETB4C9 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_setb4c9',
    instance='setb4c9',
    tier='full',
    jobs=15,
    machines=11,
    operations=150,
    candidates=165,
    raw_path=RAW_DIR / 'setb4c9.json',
    objective=914,
    case_module=CASE_MODULE,
    reference={
        'kind': 'optimum',
        'objective': 914,
        'lower_bound': 914,
        'upper_bound': 914,
    },
)

SETI5XXX = make_flexible_job_shop_case(
    benchmark_id='fjsplib_seti5xxx',
    instance='seti5xxx',
    tier='full',
    jobs=15,
    machines=18,
    operations=225,
    candidates=270,
    raw_path=RAW_DIR / 'seti5xxx.json',
    objective=1194,
    case_module=CASE_MODULE,
    reference={
        'kind': 'optimum',
        'objective': 1194,
        'lower_bound': 1194,
        'upper_bound': 1194,
    },
)

CASES = (
    MT10C1,
    MT10XXX,
    SETB4C9,
    SETI5XXX,
)
