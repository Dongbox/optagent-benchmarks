from __future__ import annotations

from benchmarks.cases.tsplib.tsp._domain import (
    make_tsp_case,
    RAW_DIR,
)

CASE_MODULE = __name__

BIER127 = make_tsp_case(
    benchmark_id='tsplib_bier127',
    instance='bier127',
    tier='calibration',
    nodes=127,
    raw_path=RAW_DIR / 'bier127.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/bier127.tsp.gz',
    objective=118282,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/bier127.tsp',),
)

CASES = (BIER127,)
