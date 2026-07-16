from __future__ import annotations

from benchmarks.cases.tsplib.tsp._domain import (
    make_tsp_case,
    RAW_DIR,
)

CASE_MODULE = __name__

ALI535 = make_tsp_case(
    benchmark_id='tsplib_ali535',
    instance='ali535',
    tier='full',
    nodes=535,
    raw_path=RAW_DIR / 'ali535.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/ali535.tsp.gz',
    objective=202339,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/ali535.tsp',),
)

CASES = (ALI535,)
