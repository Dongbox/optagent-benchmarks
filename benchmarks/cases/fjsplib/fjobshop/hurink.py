from __future__ import annotations

from benchmarks.cases.fjsplib.fjobshop._domain import (
    make_flexible_job_shop_case,
    RAW_DIR,
)

CASE_MODULE = __name__

E_MT06 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_e-mt06',
    instance='e-mt06',
    tier='calibration',
    jobs=6,
    machines=6,
    operations=36,
    candidates=42,
    raw_path=RAW_DIR / 'e-mt06.json',
    objective=55,
    case_module=CASE_MODULE,
    reference={
        'kind': 'optimum',
        'objective': 55,
        'lower_bound': 55,
        'upper_bound': 55,
    },
)

V_MT06 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_v-mt06',
    instance='v-mt06',
    tier='calibration',
    jobs=6,
    machines=6,
    operations=36,
    candidates=103,
    raw_path=RAW_DIR / 'v-mt06.json',
    objective=47,
    case_module=CASE_MODULE,
    reference={
        'kind': 'optimum',
        'objective': 47,
        'lower_bound': 47,
        'upper_bound': 47,
    },
)

E_CAR7 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_e-car7',
    instance='e-car7',
    tier='calibration',
    jobs=7,
    machines=7,
    operations=49,
    candidates=58,
    raw_path=RAW_DIR / 'e-car7.json',
    objective=6123,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 6123,
        'lower_bound': 4216,
        'upper_bound': 6123,
    },
)

E_LA03 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_e-la03',
    instance='e-la03',
    tier='calibration',
    jobs=10,
    machines=5,
    operations=50,
    candidates=59,
    raw_path=RAW_DIR / 'e-la03.json',
    objective=550,
    case_module=CASE_MODULE,
    reference={
        'kind': 'optimum',
        'objective': 550,
        'lower_bound': 550,
        'upper_bound': 550,
    },
)

V_LA05 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_v-la05',
    instance='v-la05',
    tier='calibration',
    jobs=10,
    machines=5,
    operations=50,
    candidates=119,
    raw_path=RAW_DIR / 'v-la05.json',
    objective=457,
    case_module=CASE_MODULE,
    reference={
        'kind': 'optimum',
        'objective': 457,
        'lower_bound': 457,
        'upper_bound': 457,
    },
)

E_CAR2 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_e-car2',
    instance='e-car2',
    tier='calibration',
    jobs=13,
    machines=4,
    operations=52,
    candidates=63,
    raw_path=RAW_DIR / 'e-car2.json',
    objective=6455,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 6455,
        'lower_bound': 5929,
        'upper_bound': 6455,
    },
)

V_CAR8 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_v-car8',
    instance='v-car8',
    tier='calibration',
    jobs=8,
    machines=8,
    operations=64,
    candidates=254,
    raw_path=RAW_DIR / 'v-car8.json',
    objective=4613,
    case_module=CASE_MODULE,
    reference={
        'kind': 'optimum',
        'objective': 4613,
        'lower_bound': 4613,
        'upper_bound': 4613,
    },
)

R_CAR6 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_r-car6',
    instance='r-car6',
    tier='calibration',
    jobs=8,
    machines=9,
    operations=72,
    candidates=140,
    raw_path=RAW_DIR / 'r-car6.json',
    objective=6147,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 6147,
        'lower_bound': 5486,
        'upper_bound': 6147,
    },
)

E_ABZ5 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_e-abz5',
    instance='e-abz5',
    tier='calibration',
    jobs=10,
    machines=10,
    operations=100,
    candidates=113,
    raw_path=RAW_DIR / 'e-abz5.json',
    objective=1176,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 1176,
        'lower_bound': 859,
        'upper_bound': 1176,
    },
)

E_LA11 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_e-la11',
    instance='e-la11',
    tier='calibration',
    jobs=20,
    machines=5,
    operations=100,
    candidates=113,
    raw_path=RAW_DIR / 'e-la11.json',
    objective=1103,
    case_module=CASE_MODULE,
    reference={
        'kind': 'optimum',
        'objective': 1103,
        'lower_bound': 1103,
        'upper_bound': 1103,
    },
)

R_LA17 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_r-la17',
    instance='r-la17',
    tier='calibration',
    jobs=10,
    machines=10,
    operations=100,
    candidates=193,
    raw_path=RAW_DIR / 'r-la17.json',
    objective=646,
    case_module=CASE_MODULE,
    reference={
        'kind': 'optimum',
        'objective': 646,
        'lower_bound': 646,
        'upper_bound': 646,
    },
)

V_ORB7 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_v-orb7',
    instance='v-orb7',
    tier='calibration',
    jobs=10,
    machines=10,
    operations=100,
    candidates=456,
    raw_path=RAW_DIR / 'v-orb7.json',
    objective=275,
    case_module=CASE_MODULE,
    reference={
        'kind': 'optimum',
        'objective': 275,
        'lower_bound': 275,
        'upper_bound': 275,
    },
)

V_ABZ5 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_v-abz5',
    instance='v-abz5',
    tier='calibration',
    jobs=10,
    machines=10,
    operations=100,
    candidates=467,
    raw_path=RAW_DIR / 'v-abz5.json',
    objective=860,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 860,
        'lower_bound': 859,
        'upper_bound': 860,
    },
)

V_LA27 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_v-la27',
    instance='v-la27',
    tier='full',
    jobs=20,
    machines=10,
    operations=200,
    candidates=915,
    raw_path=RAW_DIR / 'v-la27.json',
    objective=1084,
    case_module=CASE_MODULE,
    reference={
        'kind': 'optimum',
        'objective': 1084,
        'lower_bound': 1084,
        'upper_bound': 1084,
    },
)

R_LA39 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_r-la39',
    instance='r-la39',
    tier='full',
    jobs=15,
    machines=15,
    operations=225,
    candidates=436,
    raw_path=RAW_DIR / 'r-la39.json',
    objective=1011,
    case_module=CASE_MODULE,
    reference={
        'kind': 'optimum',
        'objective': 1011,
        'lower_bound': 1011,
        'upper_bound': 1011,
    },
)

E_ABZ7 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_e-abz7',
    instance='e-abz7',
    tier='full',
    jobs=20,
    machines=15,
    operations=300,
    candidates=339,
    raw_path=RAW_DIR / 'e-abz7.json',
    objective=638,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 638,
        'lower_bound': 492,
        'upper_bound': 638,
    },
)

E_LA33 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_e-la33',
    instance='e-la33',
    tier='full',
    jobs=30,
    machines=10,
    operations=300,
    candidates=339,
    raw_path=RAW_DIR / 'e-la33.json',
    objective=1547,
    case_module=CASE_MODULE,
    reference={
        'kind': 'optimum',
        'objective': 1547,
        'lower_bound': 1547,
        'upper_bound': 1547,
    },
)

V_ABZ7 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_v-abz7',
    instance='v-abz7',
    tier='full',
    jobs=20,
    machines=15,
    operations=300,
    candidates=1951,
    raw_path=RAW_DIR / 'v-abz7.json',
    objective=495,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 495,
        'lower_bound': 492,
        'upper_bound': 495,
    },
)

CASES = (
    E_MT06,
    V_MT06,
    E_CAR7,
    E_LA03,
    V_LA05,
    E_CAR2,
    V_CAR8,
    R_CAR6,
    E_ABZ5,
    E_LA11,
    R_LA17,
    V_ORB7,
    V_ABZ5,
    V_LA27,
    R_LA39,
    E_ABZ7,
    E_LA33,
    V_ABZ7,
)
