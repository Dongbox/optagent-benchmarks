from __future__ import annotations

from benchmarks.cases.tsplib.tsp._domain import (
    make_tsp_case,
    RAW_DIR,
)

CASE_MODULE = __name__

BAYG29 = make_tsp_case(
    benchmark_id='tsplib_bayg29',
    instance='bayg29',
    tier='smoke',
    nodes=29,
    raw_path=RAW_DIR / 'bayg29.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/bayg29.tsp.gz',
    objective=1610,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/bayg29.tsp',),
)

CASES = (BAYG29,)
