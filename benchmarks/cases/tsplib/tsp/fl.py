from __future__ import annotations

from benchmarks.cases.tsplib.tsp._domain import (
    make_tsp_case,
    RAW_DIR,
)

CASE_MODULE = __name__

FL417 = make_tsp_case(
    benchmark_id='tsplib_fl417',
    instance='fl417',
    tier='calibration',
    nodes=417,
    raw_path=RAW_DIR / 'fl417.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/fl417.tsp.gz',
    objective=11861,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/fl417.tsp',),
)

FL1400 = make_tsp_case(
    benchmark_id='tsplib_fl1400',
    instance='fl1400',
    tier='pressure',
    nodes=1400,
    raw_path=RAW_DIR / 'fl1400.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/fl1400.tsp.gz',
    objective=20127,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/fl1400.tsp',),
)

FL1577 = make_tsp_case(
    benchmark_id='tsplib_fl1577',
    instance='fl1577',
    tier='pressure',
    nodes=1577,
    raw_path=RAW_DIR / 'fl1577.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/fl1577.tsp.gz',
    objective=22249,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/fl1577.tsp',),
)

CASES = (FL417, FL1400, FL1577,)
