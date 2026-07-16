from __future__ import annotations

from benchmarks.cases.tsplib.tsp._domain import (
    make_tsp_case,
    RAW_DIR,
)

CASE_MODULE = __name__

PA561 = make_tsp_case(
    benchmark_id='tsplib_pa561',
    instance='pa561',
    tier='full',
    nodes=561,
    raw_path=RAW_DIR / 'pa561.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/pa561.tsp.gz',
    objective=2763,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/pa561.tsp',),
)

CASES = (PA561,)
