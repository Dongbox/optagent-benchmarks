from __future__ import annotations

from benchmarks.cases.tsplib.tsp._domain import (
    make_tsp_case,
    RAW_DIR,
)

CASE_MODULE = __name__

RAT195 = make_tsp_case(
    benchmark_id='tsplib_rat195',
    instance='rat195',
    tier='calibration',
    nodes=195,
    raw_path=RAW_DIR / 'rat195.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/rat195.tsp.gz',
    objective=2323,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/rat195.tsp',),
)

RAT575 = make_tsp_case(
    benchmark_id='tsplib_rat575',
    instance='rat575',
    tier='full',
    nodes=575,
    raw_path=RAW_DIR / 'rat575.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/rat575.tsp.gz',
    objective=6773,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/rat575.tsp',),
)

RAT783 = make_tsp_case(
    benchmark_id='tsplib_rat783',
    instance='rat783',
    tier='full',
    nodes=783,
    raw_path=RAW_DIR / 'rat783.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/rat783.tsp.gz',
    objective=8806,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/rat783.tsp',),
)

CASES = (RAT195, RAT575, RAT783)
