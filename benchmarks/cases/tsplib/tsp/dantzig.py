from __future__ import annotations

from benchmarks.cases.tsplib.tsp._domain import (
    make_tsp_case,
    RAW_DIR,
)

CASE_MODULE = __name__

DANTZIG42 = make_tsp_case(
    benchmark_id='tsplib_dantzig42',
    instance='dantzig42',
    tier='smoke',
    nodes=42,
    raw_path=RAW_DIR / 'dantzig42.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/dantzig42.tsp.gz',
    objective=699,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/dantzig42.tsp',),
)

CASES = (DANTZIG42,)
