from __future__ import annotations

from benchmarks.cases.fjsplib.fjobshop._domain import (
    make_flexible_job_shop_case,
    RAW_DIR,
)

CASE_MODULE = __name__

SFJS02 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_sfjs02',
    instance='sfjs02',
    tier='smoke',
    jobs=2,
    machines=2,
    operations=4,
    candidates=6,
    raw_path=RAW_DIR / 'sfjs02.json',
    objective=107,
    case_module=CASE_MODULE,
    reference={
        'kind': 'optimum',
        'objective': 107,
        'lower_bound': 107,
        'upper_bound': 107,
    },
)

SFJS01 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_sfjs01',
    instance='sfjs01',
    tier='smoke',
    jobs=2,
    machines=2,
    operations=4,
    candidates=8,
    raw_path=RAW_DIR / 'sfjs01.json',
    objective=66,
    case_module=CASE_MODULE,
    reference={
        'kind': 'optimum',
        'objective': 66,
        'lower_bound': 66,
        'upper_bound': 66,
    },
)

SFJS04 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_sfjs04',
    instance='sfjs04',
    tier='smoke',
    jobs=3,
    machines=2,
    operations=6,
    candidates=10,
    raw_path=RAW_DIR / 'sfjs04.json',
    objective=355,
    case_module=CASE_MODULE,
    reference={
        'kind': 'optimum',
        'objective': 355,
        'lower_bound': 355,
        'upper_bound': 355,
    },
)

SFJS05 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_sfjs05',
    instance='sfjs05',
    tier='smoke',
    jobs=3,
    machines=2,
    operations=6,
    candidates=12,
    raw_path=RAW_DIR / 'sfjs05.json',
    objective=119,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 119,
        'lower_bound': 107,
        'upper_bound': 119,
    },
)

SFJS06 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_sfjs06',
    instance='sfjs06',
    tier='smoke',
    jobs=3,
    machines=3,
    operations=9,
    candidates=15,
    raw_path=RAW_DIR / 'sfjs06.json',
    objective=320,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 320,
        'lower_bound': 310,
        'upper_bound': 320,
    },
)

SFJS07 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_sfjs07',
    instance='sfjs07',
    tier='smoke',
    jobs=3,
    machines=5,
    operations=9,
    candidates=18,
    raw_path=RAW_DIR / 'sfjs07.json',
    objective=397,
    case_module=CASE_MODULE,
    reference={
        'kind': 'optimum',
        'objective': 397,
        'lower_bound': 397,
        'upper_bound': 397,
    },
)

SFJS09 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_sfjs09',
    instance='sfjs09',
    tier='smoke',
    jobs=3,
    machines=3,
    operations=9,
    candidates=18,
    raw_path=RAW_DIR / 'sfjs09.json',
    objective=210,
    case_module=CASE_MODULE,
    reference={
        'kind': 'optimum',
        'objective': 210,
        'lower_bound': 210,
        'upper_bound': 210,
    },
)

SFJS10 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_sfjs10',
    instance='sfjs10',
    tier='smoke',
    jobs=4,
    machines=5,
    operations=12,
    candidates=20,
    raw_path=RAW_DIR / 'sfjs10.json',
    objective=516,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 516,
        'lower_bound': 427,
        'upper_bound': 516,
    },
)

MFJS02 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_mfjs02',
    instance='mfjs02',
    tier='smoke',
    jobs=5,
    machines=7,
    operations=15,
    candidates=39,
    raw_path=RAW_DIR / 'mfjs02.json',
    objective=446,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 446,
        'lower_bound': 396,
        'upper_bound': 446,
    },
)

MFJS07 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_mfjs07',
    instance='mfjs07',
    tier='calibration',
    jobs=8,
    machines=7,
    operations=32,
    candidates=78,
    raw_path=RAW_DIR / 'mfjs07.json',
    objective=879,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 879,
        'lower_bound': 764,
        'upper_bound': 879,
    },
)

CASES = (
    SFJS02,
    SFJS01,
    SFJS04,
    SFJS05,
    SFJS06,
    SFJS07,
    SFJS09,
    SFJS10,
    MFJS02,
    MFJS07,
)

