from __future__ import annotations

from benchmarks.cases.tsplib.tsp._domain import (
    make_tsp_case,
    RAW_DIR,
)

CASE_MODULE = __name__

U574 = make_tsp_case(
    benchmark_id='tsplib_u574',
    instance='u574',
    tier='full',
    nodes=574,
    raw_path=RAW_DIR / 'u574.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/u574.tsp.gz',
    objective=36905,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/u574.tsp',),
)

U724 = make_tsp_case(
    benchmark_id='tsplib_u724',
    instance='u724',
    tier='full',
    nodes=724,
    raw_path=RAW_DIR / 'u724.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/u724.tsp.gz',
    objective=41910,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/u724.tsp',),
)

U1060 = make_tsp_case(
    benchmark_id='tsplib_u1060',
    instance='u1060',
    tier='pressure',
    nodes=1060,
    raw_path=RAW_DIR / 'u1060.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/u1060.tsp.gz',
    objective=224094,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/u1060.tsp',),
)

U2152 = make_tsp_case(
    benchmark_id='tsplib_u2152',
    instance='u2152',
    tier='pressure',
    nodes=2152,
    raw_path=RAW_DIR / 'u2152.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/u2152.tsp.gz',
    objective=64253,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/u2152.tsp',),
)

CASES = (U574, U724, U1060, U2152)