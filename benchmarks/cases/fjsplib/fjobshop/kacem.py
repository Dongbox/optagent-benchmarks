from __future__ import annotations

from benchmarks.cases.fjsplib.fjobshop._domain import (
    make_flexible_job_shop_case,
    RAW_DIR,
)

CASE_MODULE = __name__

K1 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_k1',
    instance='k1',
    tier='smoke',
    jobs=4,
    machines=5,
    operations=12,
    candidates=60,
    raw_path=RAW_DIR / 'k1.json',
    objective=11,
    case_module=CASE_MODULE,
    reference={
        'kind': 'optimum',
        'objective': 11,
        'lower_bound': 11,
        'upper_bound': 11,
    },
)

K2 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_k2',
    instance='k2',
    tier='smoke',
    jobs=10,
    machines=7,
    operations=29,
    candidates=203,
    raw_path=RAW_DIR / 'k2.json',
    objective=11,
    case_module=CASE_MODULE,
    reference={
        'kind': 'optimum',
        'objective': 11,
        'lower_bound': 11,
        'upper_bound': 11,
    },
)

K3 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_k3',
    instance='k3',
    tier='smoke',
    jobs=10,
    machines=10,
    operations=30,
    candidates=300,
    raw_path=RAW_DIR / 'k3.json',
    objective=7,
    case_module=CASE_MODULE,
    reference={
        'kind': 'optimum',
        'objective': 7,
        'lower_bound': 7,
        'upper_bound': 7,
    },
)

K4 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_k4',
    instance='k4',
    tier='calibration',
    jobs=15,
    machines=10,
    operations=56,
    candidates=560,
    raw_path=RAW_DIR / 'k4.json',
    objective=12,
    case_module=CASE_MODULE,
    reference={
        'kind': 'optimum',
        'objective': 12,
        'lower_bound': 12,
        'upper_bound': 12,
    },
)

CASES = (
    K1,
    K2,
    K3,
    K4,
)
