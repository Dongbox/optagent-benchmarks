from __future__ import annotations

from benchmarks.cases.tsplib.tsp._domain import (
    make_tsp_case,
    RAW_DIR,
)

CASE_MODULE = __name__

BRAZIL58 = make_tsp_case(
    benchmark_id='tsplib_brazil58',
    instance='brazil58',
    tier='smoke',
    nodes=58,
    raw_path=RAW_DIR / 'brazil58.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/brazil58.tsp.gz',
    objective=25395,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/brazil58.tsp',),
)

CASES = (BRAZIL58,)
