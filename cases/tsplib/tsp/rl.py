from __future__ import annotations

from benchmarks.cases.tsplib.tsp._domain import (
    make_tsp_case,
    RAW_DIR,
)

CASE_MODULE = __name__

RL1304 = make_tsp_case(
    benchmark_id='tsplib_rl1304',
    instance='rl1304',
    tier='pressure',
    nodes=1304,
    raw_path=RAW_DIR / 'rl1304.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/rl1304.tsp.gz',
    objective=252948,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/rl1304.tsp',),
)

CASES = (RL1304,)
