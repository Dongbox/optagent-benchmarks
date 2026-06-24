from __future__ import annotations

from benchmarks.cases.tsplib.tsp._domain import (
    make_tsp_case,
    RAW_DIR,
)

CASE_MODULE = __name__

EIL51 = make_tsp_case(
    benchmark_id='tsplib_eil51',
    instance='eil51',
    tier='smoke',
    nodes=51,
    raw_path=RAW_DIR / 'eil51.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/eil51.tsp.gz',
    objective=426,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/eil51.tsp',),
)

CASES = (EIL51,)
