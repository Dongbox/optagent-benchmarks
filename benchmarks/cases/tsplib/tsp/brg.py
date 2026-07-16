from __future__ import annotations

from benchmarks.cases.tsplib.tsp._domain import (
    make_tsp_case,
    RAW_DIR,
)

CASE_MODULE = __name__

BRG180 = make_tsp_case(
    benchmark_id='tsplib_brg180',
    instance='brg180',
    tier='calibration',
    nodes=180,
    raw_path=RAW_DIR / 'brg180.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/brg180.tsp.gz',
    objective=1950,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/brg180.tsp',),
)

CASES = (BRG180,)
