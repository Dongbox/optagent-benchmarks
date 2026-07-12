from __future__ import annotations

from benchmarks.cases.tsplib.tsp._domain import (
    make_tsp_case,
    RAW_DIR,
)

CASE_MODULE = __name__

RD400 = make_tsp_case(
    benchmark_id='tsplib_rd400',
    instance='rd400',
    tier='calibration',
    nodes=400,
    raw_path=RAW_DIR / 'rd400.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/rd400.tsp.gz',
    objective=15281,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/rd400.tsp',),
)

CASES = (RD400,)
