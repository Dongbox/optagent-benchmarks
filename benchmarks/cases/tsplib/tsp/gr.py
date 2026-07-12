from __future__ import annotations

from benchmarks.cases.tsplib.tsp._domain import (
    make_tsp_case,
    RAW_DIR,
)

CASE_MODULE = __name__

GR48 = make_tsp_case(
    benchmark_id='tsplib_gr48',
    instance='gr48',
    tier='smoke',
    nodes=48,
    raw_path=RAW_DIR / 'gr48.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/gr48.tsp.gz',
    objective=5046,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/gr48.tsp',),
)

GR431 = make_tsp_case(
    benchmark_id='tsplib_gr431',
    instance='gr431',
    tier='calibration',
    nodes=431,
    raw_path=RAW_DIR / 'gr431.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/gr431.tsp.gz',
    objective=171414,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/gr431.tsp',),
)

GR666 = make_tsp_case(
    benchmark_id='tsplib_gr666',
    instance='gr666',
    tier='full',
    nodes=666,
    raw_path=RAW_DIR / 'gr666.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/gr666.tsp.gz',
    objective=294358,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/gr666.tsp',),
)

CASES = (GR48, GR431, GR666)
