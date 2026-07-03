from __future__ import annotations

from benchmarks.cases.tsplib.tsp._domain import (
    make_tsp_case,
    RAW_DIR,
)

CASE_MODULE = __name__

LIN318 = make_tsp_case(
    benchmark_id='tsplib_lin318',
    instance='lin318',
    tier='calibration',
    nodes=318,
    raw_path=RAW_DIR / 'lin318.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/lin318.tsp.gz',
    objective=42029,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/lin318.tsp',),
)

CASES = (LIN318,)
