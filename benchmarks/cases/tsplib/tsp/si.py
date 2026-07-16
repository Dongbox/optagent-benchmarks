from __future__ import annotations

from benchmarks.cases.tsplib.tsp._domain import (
    make_tsp_case,
    RAW_DIR,
)

CASE_MODULE = __name__

SI175 = make_tsp_case(
    benchmark_id='tsplib_si175',
    instance='si175',
    tier='calibration',
    nodes=175,
    raw_path=RAW_DIR / 'si175.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/si175.tsp.gz',
    objective=21407,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/si175.tsp',),
)

SI535 = make_tsp_case(
    benchmark_id='tsplib_si535',
    instance='si535',
    tier='full',
    nodes=535,
    raw_path=RAW_DIR / 'si535.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/si535.tsp.gz',
    objective=48450,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/si535.tsp',),
)

SI1032 = make_tsp_case(
    benchmark_id='tsplib_si1032',
    instance='si1032',
    tier='pressure',
    nodes=1032,
    raw_path=RAW_DIR / 'si1032.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/si1032.tsp.gz',
    objective=92650,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/si1032.tsp',),
)

CASES = (SI175, SI535, SI1032,)
