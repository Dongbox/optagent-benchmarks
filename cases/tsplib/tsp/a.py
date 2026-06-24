from __future__ import annotations

from benchmarks.cases.tsplib.tsp._domain import (
    make_tsp_case,
    RAW_DIR,
)

CASE_MODULE = __name__

A280 = make_tsp_case(
    benchmark_id='tsplib_a280',
    instance='a280',
    tier='full',
    nodes=280,
    raw_path=RAW_DIR / 'a280.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/a280.tsp.gz',
    objective=2579,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/a280.tsp',),
)

CASES = (A280,)
