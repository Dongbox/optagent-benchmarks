from __future__ import annotations

from benchmarks.cases.tsplib.tsp._domain import (
    make_tsp_case,
    RAW_DIR,
)

CASE_MODULE = __name__

VM1084 = make_tsp_case(
    benchmark_id='tsplib_vm1084',
    instance='vm1084',
    tier='pressure',
    nodes=1084,
    raw_path=RAW_DIR / 'vm1084.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/vm1084.tsp.gz',
    objective=239297,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/vm1084.tsp',),
)

CASES = (VM1084,)
