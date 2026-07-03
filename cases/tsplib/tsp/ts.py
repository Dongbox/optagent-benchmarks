from __future__ import annotations

from benchmarks.cases.tsplib.tsp._domain import (
    make_tsp_case,
    RAW_DIR,
)

CASE_MODULE = __name__

TS225 = make_tsp_case(
    benchmark_id='tsplib_ts225',
    instance='ts225',
    tier='calibration',
    nodes=225,
    raw_path=RAW_DIR / 'ts225.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/ts225.tsp.gz',
    objective=126643,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/ts225.tsp',),
)

CASES = (TS225,)
