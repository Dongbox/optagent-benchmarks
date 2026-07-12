from __future__ import annotations

from benchmarks.cases.tsplib.tsp._domain import (
    make_tsp_case,
    RAW_DIR,
)

CASE_MODULE = __name__

DSJ1000 = make_tsp_case(
    benchmark_id='tsplib_dsj1000',
    instance='dsj1000',
    tier='full',
    nodes=1000,
    raw_path=RAW_DIR / 'dsj1000.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/dsj1000.tsp.gz',
    objective=18660188,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/dsj1000.tsp',),
)

CASES = (DSJ1000,)
