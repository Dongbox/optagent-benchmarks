from __future__ import annotations

from benchmarks.cases.fjsplib.fjobshop._domain import (
    make_flexible_job_shop_case,
    RAW_DIR,
)

CASE_MODULE = __name__

SETB4C9 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_setb4c9',
    instance='setb4c9',
    tier='calibration',
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
    SETB4C9,
    SETI5XXX,
)
