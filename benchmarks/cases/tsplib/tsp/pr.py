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

PR107 = make_tsp_case(
    benchmark_id='tsplib_pr107',
    instance='pr107',
    tier='calibration',
    nodes=107,
    raw_path=RAW_DIR / 'pr107.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/pr107.tsp.gz',
    objective=44303,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/pr107.tsp',),
)

PR124 = make_tsp_case(
    benchmark_id='tsplib_pr124',
    instance='pr124',
    tier='calibration',
    nodes=124,
    raw_path=RAW_DIR / 'pr124.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/pr124.tsp.gz',
    objective=59030,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/pr124.tsp',),
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

PR226 = make_tsp_case(
    benchmark_id='tsplib_pr226',
    instance='pr226',
    tier='calibration',
    nodes=226,
    raw_path=RAW_DIR / 'pr226.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/pr226.tsp.gz',
    objective=80369,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/pr226.tsp',),
)

PR264 = make_tsp_case(
    benchmark_id='tsplib_pr264',
    instance='pr264',
    tier='calibration',
    nodes=264,
    raw_path=RAW_DIR / 'pr264.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/pr264.tsp.gz',
    objective=49135,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/pr264.tsp',),
)

PR439 = make_tsp_case(
    benchmark_id='tsplib_pr439',
    instance='pr439',
    tier='calibration',
    nodes=439,
    raw_path=RAW_DIR / 'pr439.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/pr439.tsp.gz',
    objective=107217,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/pr439.tsp',),
)

CASES = (PR76, PR107, PR124, PR152, PR226, PR264, PR439,)
