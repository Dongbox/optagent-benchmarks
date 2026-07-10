from __future__ import annotations

from benchmarks.cases.fjsplib.fjobshop._domain import (
    make_flexible_job_shop_case,
    RAW_DIR,
)

CASE_MODULE = __name__

MK01 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_mk01',
    instance='mk01',
    tier='calibration',
    jobs=10,
    machines=6,
    operations=55,
    candidates=115,
    raw_path=RAW_DIR / 'mk01.json',
    objective=40,
    case_module=CASE_MODULE,
    reference={
        'kind': 'optimum',
        'objective': 40,
        'lower_bound': 40,
        'upper_bound': 40,
    },
)

MK02 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_mk02',
    instance='mk02',
    tier='calibration',
    jobs=10,
    machines=6,
    operations=58,
    candidates=238,
    raw_path=RAW_DIR / 'mk02.json',
    objective=26,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 26,
        'lower_bound': 24,
        'upper_bound': 26,
    },
)

MK04 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_mk04',
    instance='mk04',
    tier='calibration',
    jobs=15,
    machines=8,
    operations=90,
    candidates=172,
    raw_path=RAW_DIR / 'mk04.json',
    objective=60,
    case_module=CASE_MODULE,
    reference={
        'kind': 'optimum',
        'objective': 60,
        'lower_bound': 60,
        'upper_bound': 60,
    },
)

MK07 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_mk07',
    instance='mk07',
    tier='calibration',
    jobs=20,
    machines=5,
    operations=100,
    candidates=283,
    raw_path=RAW_DIR / 'mk07.json',
    objective=139,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 139,
        'lower_bound': 133,
        'upper_bound': 139,
    },
)

MK05 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_mk05',
    instance='mk05',
    tier='full',
    jobs=15,
    machines=4,
    operations=106,
    candidates=181,
    raw_path=RAW_DIR / 'mk05.json',
    objective=172,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 172,
        'lower_bound': 168,
        'upper_bound': 172,
    },
)

MK03 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_mk03',
    instance='mk03',
    tier='full',
    jobs=15,
    machines=8,
    operations=150,
    candidates=451,
    raw_path=RAW_DIR / 'mk03.json',
    objective=204,
    case_module=CASE_MODULE,
    reference={
        'kind': 'optimum',
        'objective': 204,
        'lower_bound': 204,
        'upper_bound': 204,
    },
)

MK06 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_mk06',
    instance='mk06',
    tier='full',
    jobs=10,
    machines=10,
    operations=150,
    candidates=490,
    raw_path=RAW_DIR / 'mk06.json',
    objective=58,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 58,
        'lower_bound': 33,
        'upper_bound': 58,
    },
)

MK11 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_mk11',
    instance='mk11',
    tier='full',
    jobs=30,
    machines=5,
    operations=179,
    candidates=270,
    raw_path=RAW_DIR / 'mk11.json',
    objective=615,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 615,
        'lower_bound': 594,
        'upper_bound': 615,
    },
)

MK12 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_mk12',
    instance='mk12',
    tier='full',
    jobs=30,
    machines=10,
    operations=193,
    candidates=288,
    raw_path=RAW_DIR / 'mk12.json',
    objective=508,
    case_module=CASE_MODULE,
    reference={
        'kind': 'optimum',
        'objective': 508,
        'lower_bound': 508,
        'upper_bound': 508,
    },
)

MK08 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_mk08',
    instance='mk08',
    tier='full',
    jobs=20,
    machines=10,
    operations=225,
    candidates=322,
    raw_path=RAW_DIR / 'mk08.json',
    objective=523,
    case_module=CASE_MODULE,
    reference={
        'kind': 'optimum',
        'objective': 523,
        'lower_bound': 523,
        'upper_bound': 523,
    },
)

MK13 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_mk13',
    instance='mk13',
    tier='full',
    jobs=30,
    machines=10,
    operations=231,
    candidates=778,
    raw_path=RAW_DIR / 'mk13.json',
    objective=430,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 430,
        'lower_bound': 353,
        'upper_bound': 430,
    },
)

MK09 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_mk09',
    instance='mk09',
    tier='full',
    jobs=20,
    machines=10,
    operations=240,
    candidates=606,
    raw_path=RAW_DIR / 'mk09.json',
    objective=307,
    case_module=CASE_MODULE,
    reference={
        'kind': 'optimum',
        'objective': 307,
        'lower_bound': 307,
        'upper_bound': 307,
    },
)

MK10 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_mk10',
    instance='mk10',
    tier='full',
    jobs=20,
    machines=15,
    operations=240,
    candidates=716,
    raw_path=RAW_DIR / 'mk10.json',
    objective=197,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 197,
        'lower_bound': 175,
        'upper_bound': 197,
    },
)

MK14 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_mk14',
    instance='mk14',
    tier='full',
    jobs=30,
    machines=15,
    operations=277,
    candidates=432,
    raw_path=RAW_DIR / 'mk14.json',
    objective=694,
    case_module=CASE_MODULE,
    reference={
        'kind': 'optimum',
        'objective': 694,
        'lower_bound': 694,
        'upper_bound': 694,
    },
)

CASES = (
    MK01,
    MK02,
    MK04,
    MK07,
    MK05,
    MK03,
    MK06,
    MK11,
    MK12,
    MK08,
    MK13,
    MK09,
    MK10,
    MK14,
)
