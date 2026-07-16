from __future__ import annotations

from benchmarks.cases.fjsplib.fjobshop._domain import (
    make_flexible_job_shop_case,
    RAW_DIR,
)

CASE_MODULE = __name__

DPP03 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_dpp03',
    instance='dpp03',
    tier='pressure',
    jobs=10,
    machines=5,
    operations=196,
    candidates=501,
    raw_path=RAW_DIR / 'dpp03.json',
    objective=2229,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 2229,
        'lower_bound': 2228,
        'upper_bound': 2229,
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

CASES = (
    DPP03,
    DPP05,
    DPP16,
)
