from __future__ import annotations

from benchmarks.cases.fjsplib.fjobshop._domain import (
    make_flexible_job_shop_case,
    RAW_DIR,
)

CASE_MODULE = __name__

DPP01 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_dpp01',
    instance='dpp01',
    tier='full',
    jobs=10,
    machines=5,
    operations=196,
    candidates=221,
    raw_path=RAW_DIR / 'dpp01.json',
    objective=2518,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 2518,
        'lower_bound': 2505,
        'upper_bound': 2518,
    },
)

DPP04 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_dpp04',
    instance='dpp04',
    tier='full',
    jobs=10,
    machines=5,
    operations=196,
    candidates=221,
    raw_path=RAW_DIR / 'dpp04.json',
    objective=2503,
    case_module=CASE_MODULE,
    reference={
        'kind': 'optimum',
        'objective': 2503,
        'lower_bound': 2503,
        'upper_bound': 2503,
    },
)

DPP05 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_dpp05',
    instance='dpp05',
    tier='full',
    jobs=10,
    machines=5,
    operations=196,
    candidates=332,
    raw_path=RAW_DIR / 'dpp05.json',
    objective=2216,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 2216,
        'lower_bound': 2189,
        'upper_bound': 2216,
    },
)

DPP09 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_dpp09',
    instance='dpp09',
    tier='full',
    jobs=15,
    machines=8,
    operations=293,
    candidates=1182,
    raw_path=RAW_DIR / 'dpp09.json',
    objective=2066,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 2066,
        'lower_bound': 2061,
        'upper_bound': 2066,
    },
)

DPP13 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_dpp13',
    instance='dpp13',
    tier='pressure',
    jobs=20,
    machines=10,
    operations=387,
    candidates=518,
    raw_path=RAW_DIR / 'dpp13.json',
    objective=2257,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 2257,
        'lower_bound': 2161,
        'upper_bound': 2257,
    },
)

DPP16 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_dpp16',
    instance='dpp16',
    tier='pressure',
    jobs=20,
    machines=10,
    operations=387,
    candidates=518,
    raw_path=RAW_DIR / 'dpp16.json',
    objective=2255,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 2255,
        'lower_bound': 2148,
        'upper_bound': 2255,
    },
)

DPP17 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_dpp17',
    instance='dpp17',
    tier='pressure',
    jobs=20,
    machines=10,
    operations=387,
    candidates=1156,
    raw_path=RAW_DIR / 'dpp17.json',
    objective=2140,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 2140,
        'lower_bound': 2088,
        'upper_bound': 2140,
    },
)

DPP15 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_dpp15',
    instance='dpp15',
    tier='pressure',
    jobs=20,
    machines=10,
    operations=387,
    candidates=1941,
    raw_path=RAW_DIR / 'dpp15.json',
    objective=2165,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 2165,
        'lower_bound': 2161,
        'upper_bound': 2165,
    },
)

CASES = (
    DPP01,
    DPP04,
    DPP05,
    DPP09,
    DPP13,
    DPP16,
    DPP17,
    DPP15,
)
