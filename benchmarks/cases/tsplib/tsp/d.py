from __future__ import annotations

from benchmarks.cases.tsplib.tsp._domain import (
    make_tsp_case,
    RAW_DIR,
)

CASE_MODULE = __name__

D198 = make_tsp_case(
    benchmark_id='tsplib_d198',
    instance='d198',
    tier='calibration',
    nodes=198,
    raw_path=RAW_DIR / 'd198.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/d198.tsp.gz',
    objective=15780,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/d198.tsp',),
)

D657 = make_tsp_case(
    benchmark_id='tsplib_d657',
    instance='d657',
    tier='full',
    nodes=657,
    raw_path=RAW_DIR / 'd657.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/d657.tsp.gz',
    objective=48912,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/d657.tsp',),
)

D1655 = make_tsp_case(
    benchmark_id='tsplib_d1655',
    instance='d1655',
    tier='pressure',
    nodes=1655,
    raw_path=RAW_DIR / 'd1655.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/d1655.tsp.gz',
    objective=62128,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/d1655.tsp',),
)

CASES = (D198, D657, D1655,)
