from __future__ import annotations

from benchmarks.cases.tsplib.tsp._domain import (
    make_tsp_case,
    RAW_DIR,
)

CASE_MODULE = __name__

PR76 = make_tsp_case(
    benchmark_id='tsplib_pr76',
    instance='pr76',
    tier='smoke',
    nodes=76,
    raw_path=RAW_DIR / 'pr76.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/pr76.tsp.gz',
    objective=108159,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/pr76.tsp',),
)

PR152 = make_tsp_case(
    benchmark_id='tsplib_pr152',
    instance='pr152',
    tier='calibration',
    nodes=152,
    raw_path=RAW_DIR / 'pr152.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/pr152.tsp.gz',
    objective=73682,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/pr152.tsp',),
)

PR1002 = make_tsp_case(
    benchmark_id='tsplib_pr1002',
    instance='pr1002',
    tier='pressure',
    nodes=1002,
    raw_path=RAW_DIR / 'pr1002.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/pr1002.tsp.gz',
    objective=259045,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/pr1002.tsp',),
)

PR2392 = make_tsp_case(
    benchmark_id='tsplib_pr2392',
    instance='pr2392',
    tier='pressure',
    nodes=2392,
    raw_path=RAW_DIR / 'pr2392.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/pr2392.tsp.gz',
    objective=378032,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/pr2392.tsp',),
)

CASES = (PR76, PR152, PR1002, PR2392)
