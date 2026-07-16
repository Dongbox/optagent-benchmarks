from __future__ import annotations

from benchmarks.cases.tsplib.tsp._domain import (
    make_tsp_case,
    RAW_DIR,
)

CASE_MODULE = __name__

BAYS29 = make_tsp_case(
    benchmark_id='tsplib_bays29',
    instance='bays29',
    tier='smoke',
    nodes=29,
    raw_path=RAW_DIR / 'bays29.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/bays29.tsp.gz',
    objective=2020,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/bays29.tsp',),
)

CASES = (BAYS29,)
