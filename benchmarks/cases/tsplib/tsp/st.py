from __future__ import annotations

from benchmarks.cases.tsplib.tsp._domain import (
    make_tsp_case,
    RAW_DIR,
)

CASE_MODULE = __name__

ST70 = make_tsp_case(
    benchmark_id='tsplib_st70',
    instance='st70',
    tier='smoke',
    nodes=70,
    raw_path=RAW_DIR / 'st70.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/st70.tsp.gz',
    objective=675,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/st70.tsp',),
)

CASES = (ST70,)
