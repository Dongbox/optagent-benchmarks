from __future__ import annotations

from benchmarks.cases.tsplib.tsp._domain import (
    make_tsp_case,
    RAW_DIR,
)

CASE_MODULE = __name__

FRI26 = make_tsp_case(
    benchmark_id='tsplib_fri26',
    instance='fri26',
    tier='smoke',
    nodes=26,
    raw_path=RAW_DIR / 'fri26.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/fri26.tsp.gz',
    objective=937,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/fri26.tsp',),
)

CASES = (FRI26,)
