from __future__ import annotations

from benchmarks.cases.tsplib.tsp._domain import (
    make_tsp_case,
    RAW_DIR,
)

CASE_MODULE = __name__

P654 = make_tsp_case(
    benchmark_id='tsplib_p654',
    instance='p654',
    tier='full',
    nodes=654,
    raw_path=RAW_DIR / 'p654.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/p654.tsp.gz',
    objective=34643,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/p654.tsp',),
)

CASES = (P654,)
