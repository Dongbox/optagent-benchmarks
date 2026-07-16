from __future__ import annotations

from benchmarks.cases.tsplib.tsp._domain import (
    make_tsp_case,
    RAW_DIR,
)

CASE_MODULE = __name__

LIN105 = make_tsp_case(
    benchmark_id='tsplib_lin105',
    instance='lin105',
    tier='calibration',
    nodes=105,
    raw_path=RAW_DIR / 'lin105.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/lin105.tsp.gz',
    objective=14379,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/lin105.tsp',),
)

CASES = (LIN105,)
