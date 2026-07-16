from __future__ import annotations

from benchmarks.cases.tsplib.tsp._domain import (
    make_tsp_case,
    RAW_DIR,
)

CASE_MODULE = __name__

KROC100 = make_tsp_case(
    benchmark_id='tsplib_kroc100',
    instance='kroc100',
    tier='smoke',
    nodes=100,
    raw_path=RAW_DIR / 'kroc100.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/kroC100.tsp.gz',
    objective=20749,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/kroC100.tsp',),
)

CASES = (KROC100,)
