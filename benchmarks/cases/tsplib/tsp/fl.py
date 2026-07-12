from __future__ import annotations

from benchmarks.cases.tsplib.tsp._domain import (
    make_tsp_case,
    RAW_DIR,
)

CASE_MODULE = __name__

FL1577 = make_tsp_case(
    benchmark_id='tsplib_fl1577',
    instance='fl1577',
    tier='pressure',
    nodes=1577,
    raw_path=RAW_DIR / 'fl1577.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/fl1577.tsp.gz',
    objective=22249,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/fl1577.tsp',),
)

CASES = (FL1577,)
