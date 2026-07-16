from __future__ import annotations

from benchmarks.cases.tsplib.tsp._domain import (
    make_tsp_case,
    RAW_DIR,
)

CASE_MODULE = __name__

ULYSSES16 = make_tsp_case(
    benchmark_id='tsplib_ulysses16',
    instance='ulysses16',
    tier='smoke',
    nodes=16,
    raw_path=RAW_DIR / 'ulysses16.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/ulysses16.tsp.gz',
    objective=6859,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/ulysses16.tsp',),
)

ULYSSES22 = make_tsp_case(
    benchmark_id='tsplib_ulysses22',
    instance='ulysses22',
    tier='smoke',
    nodes=22,
    raw_path=RAW_DIR / 'ulysses22.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/ulysses22.tsp.gz',
    objective=7013,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/ulysses22.tsp',),
)

CASES = (ULYSSES16, ULYSSES22,)
