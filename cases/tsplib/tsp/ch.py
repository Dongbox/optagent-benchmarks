from __future__ import annotations

from benchmarks.cases.tsplib.tsp._domain import (
    make_tsp_case,
    RAW_DIR,
)

CASE_MODULE = __name__

CH130 = make_tsp_case(
    benchmark_id='tsplib_ch130',
    instance='ch130',
    tier='calibration',
    nodes=130,
    raw_path=RAW_DIR / 'ch130.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/ch130.tsp.gz',
    objective=6110,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/ch130.tsp',),
)

CASES = (CH130,)
