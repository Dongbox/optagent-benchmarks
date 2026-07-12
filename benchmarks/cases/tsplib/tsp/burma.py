from __future__ import annotations

from benchmarks.cases.tsplib.tsp._domain import (
    make_tsp_case,
    RAW_DIR,
)

CASE_MODULE = __name__

BURMA14 = make_tsp_case(
    benchmark_id='tsplib_burma14',
    instance='burma14',
    tier='smoke',
    nodes=14,
    raw_path=RAW_DIR / 'burma14.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/burma14.tsp.gz',
    objective=3323,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/burma14.tsp',),
)

CASES = (BURMA14,)
