from __future__ import annotations

from benchmarks.cases.tsplib.tsp._domain import (
    make_tsp_case,
    RAW_DIR,
)

CASE_MODULE = __name__

ATT48 = make_tsp_case(
    benchmark_id='tsplib_att48',
    instance='att48',
    tier='smoke',
    nodes=48,
    raw_path=RAW_DIR / 'att48.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/att48.tsp.gz',
    objective=10628,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/att48.tsp',),
)

ATT532 = make_tsp_case(
    benchmark_id='tsplib_att532',
    instance='att532',
    tier='full',
    nodes=532,
    raw_path=RAW_DIR / 'att532.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/att532.tsp.gz',
    objective=27686,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/att532.tsp',),
)

CASES = (ATT48, ATT532)
