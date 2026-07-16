from __future__ import annotations

from benchmarks.cases.tsplib.tsp._domain import (
    make_tsp_case,
    RAW_DIR,
)

CASE_MODULE = __name__

RL1889 = make_tsp_case(
    benchmark_id='tsplib_rl1889',
    instance='rl1889',
    tier='pressure',
    nodes=1889,
    raw_path=RAW_DIR / 'rl1889.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/rl1889.tsp.gz',
    objective=316536,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/rl1889.tsp',),
)

CASES = (RL1889,)
