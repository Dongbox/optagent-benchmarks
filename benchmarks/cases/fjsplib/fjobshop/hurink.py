from __future__ import annotations

from benchmarks.cases.fjsplib.fjobshop._domain import (
    make_flexible_job_shop_case,
    RAW_DIR,
)

CASE_MODULE = __name__

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

E_CAR2 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_e-car2',
    instance='e-car2',
    tier='smoke',
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

E_CAR3 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_e-car3',
    instance='e-car3',
    tier='smoke',
    jobs=12,
    machines=5,
    operations=60,
    candidates=71,
    raw_path=RAW_DIR / 'e-car3.json',
    objective=6856,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 6856,
        'lower_bound': 5597,
        'upper_bound': 6856,
    },
)

E_CAR5 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_e-car5',
    instance='e-car5',
    tier='smoke',
    jobs=10,
    machines=6,
    operations=60,
    candidates=70,
    raw_path=RAW_DIR / 'e-car5.json',
    objective=7229,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 7229,
        'lower_bound': 4909,
        'upper_bound': 7229,
    },
)

E_CAR7 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_e-car7',
    instance='e-car7',
    tier='smoke',
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

E_CAR8 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_e-car8',
    instance='e-car8',
    tier='smoke',
    jobs=8,
    machines=8,
    operations=64,
    candidates=75,
    raw_path=RAW_DIR / 'e-car8.json',
    objective=7689,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 7689,
        'lower_bound': 4613,
        'upper_bound': 7689,
    },
)

E_LA03 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_e-la03',
    instance='e-la03',
    tier='smoke',
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

E_MT06 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_e-mt06',
    instance='e-mt06',
    tier='smoke',
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

R_ABZ9 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_r-abz9',
    instance='r-abz9',
    tier='pressure',
    jobs=20,
    machines=15,
    operations=300,
    candidates=584,
    raw_path=RAW_DIR / 'r-abz9.json',
    objective=562,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 562,
        'lower_bound': 497,
        'upper_bound': 562,
    },
)

R_CAR3 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_r-car3',
    instance='r-car3',
    tier='calibration',
    jobs=12,
    machines=5,
    operations=60,
    candidates=121,
    raw_path=RAW_DIR / 'r-car3.json',
    objective=5626,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 5626,
        'lower_bound': 5597,
        'upper_bound': 5626,
    },
)

R_CAR4 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_r-car4',
    instance='r-car4',
    tier='calibration',
    jobs=14,
    machines=4,
    operations=56,
    candidates=110,
    raw_path=RAW_DIR / 'r-car4.json',
    objective=6518,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 6518,
        'lower_bound': 6514,
        'upper_bound': 6518,
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

R_CAR7 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_r-car7',
    instance='r-car7',
    tier='calibration',
    jobs=7,
    machines=7,
    operations=49,
    candidates=102,
    raw_path=RAW_DIR / 'r-car7.json',
    objective=4432,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 4432,
        'lower_bound': 4216,
        'upper_bound': 4432,
    },
)

R_CAR8 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_r-car8',
    instance='r-car8',
    tier='calibration',
    jobs=8,
    machines=8,
    operations=64,
    candidates=123,
    raw_path=RAW_DIR / 'r-car8.json',
    objective=5692,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 5692,
        'lower_bound': 4613,
        'upper_bound': 5692,
    },
)

R_LA01 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_r-la01',
    instance='r-la01',
    tier='calibration',
    jobs=10,
    machines=5,
    operations=50,
    candidates=96,
    raw_path=RAW_DIR / 'r-la01.json',
    objective=571,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 571,
        'lower_bound': 570,
        'upper_bound': 571,
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

R_MT06 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_r-mt06',
    instance='r-mt06',
    tier='smoke',
    jobs=6,
    machines=6,
    operations=36,
    candidates=74,
    raw_path=RAW_DIR / 'r-mt06.json',
    objective=47,
    case_module=CASE_MODULE,
    reference={
        'kind': 'optimum',
        'objective': 47,
        'lower_bound': 47,
        'upper_bound': 47,
    },
)

V_ABZ5 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_v-abz5',
    instance='v-abz5',
    tier='full',
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

V_CAR2 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_v-car2',
    instance='v-car2',
    tier='calibration',
    jobs=13,
    machines=4,
    operations=52,
    candidates=119,
    raw_path=RAW_DIR / 'v-car2.json',
    objective=5930,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 5930,
        'lower_bound': 5929,
        'upper_bound': 5930,
    },
)

V_CAR5 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_v-car5',
    instance='v-car5',
    tier='calibration',
    jobs=10,
    machines=6,
    operations=60,
    candidates=170,
    raw_path=RAW_DIR / 'v-car5.json',
    objective=4932,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 4932,
        'lower_bound': 4909,
        'upper_bound': 4932,
    },
)

V_CAR7 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_v-car7',
    instance='v-car7',
    tier='calibration',
    jobs=7,
    machines=7,
    operations=49,
    candidates=169,
    raw_path=RAW_DIR / 'v-car7.json',
    objective=4281,
    case_module=CASE_MODULE,
    reference={
        'kind': 'bounds',
        'objective': 4281,
        'lower_bound': 4216,
        'upper_bound': 4281,
    },
)

V_CAR8 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_v-car8',
    instance='v-car8',
    tier='full',
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

V_LA08 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_v-la08',
    instance='v-la08',
    tier='calibration',
    jobs=15,
    machines=5,
    operations=75,
    candidates=194,
    raw_path=RAW_DIR / 'v-la08.json',
    objective=765,
    case_module=CASE_MODULE,
    reference={
        'kind': 'optimum',
        'objective': 765,
        'lower_bound': 765,
        'upper_bound': 765,
    },
)

V_LA27 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_v-la27',
    instance='v-la27',
    tier='pressure',
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

V_ORB7 = make_flexible_job_shop_case(
    benchmark_id='fjsplib_v-orb7',
    instance='v-orb7',
    tier='full',
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

CASES = (
    E_ABZ5,
    E_CAR2,
    E_CAR3,
    E_CAR5,
    E_CAR7,
    E_CAR8,
    E_LA03,
    E_LA11,
    E_LA33,
    E_MT06,
    R_ABZ9,
    R_CAR3,
    R_CAR4,
    R_CAR6,
    R_CAR7,
    R_CAR8,
    R_LA01,
    R_LA17,
    R_MT06,
    V_ABZ5,
    V_CAR2,
    V_CAR5,
    V_CAR7,
    V_CAR8,
    V_LA05,
    V_LA08,
    V_LA27,
    V_MT06,
    V_ORB7,
)
