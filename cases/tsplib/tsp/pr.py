from __future__ import annotations

from benchmarks.cases.tsplib.tsp._domain import (
    make_tsp_case,
    RAW_DIR,
)

CASE_MODULE = __name__

PR76 = make_tsp_case(
    benchmark_id='tsplib_pr76',
    instance='pr76',
    tier='calibration',
    nodes=76,
    raw_path=RAW_DIR / 'pr76.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/pr76.tsp.gz',
    objective=108159,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/pr76.tsp',),
)

CASES = (PR76,)
