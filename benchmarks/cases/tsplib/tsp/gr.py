from __future__ import annotations

from benchmarks.cases.tsplib.tsp._domain import (
    make_tsp_case,
    RAW_DIR,
)

CASE_MODULE = __name__

GR17 = make_tsp_case(
    benchmark_id='tsplib_gr17',
    instance='gr17',
    tier='smoke',
    nodes=17,
    raw_path=RAW_DIR / 'gr17.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/gr17.tsp.gz',
    objective=2085,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/gr17.tsp',),
)

GR21 = make_tsp_case(
    benchmark_id='tsplib_gr21',
    instance='gr21',
    tier='smoke',
    nodes=21,
    raw_path=RAW_DIR / 'gr21.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/gr21.tsp.gz',
    objective=2707,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/gr21.tsp',),
)

GR24 = make_tsp_case(
    benchmark_id='tsplib_gr24',
    instance='gr24',
    tier='smoke',
    nodes=24,
    raw_path=RAW_DIR / 'gr24.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/gr24.tsp.gz',
    objective=1272,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/gr24.tsp',),
)

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

GR96 = make_tsp_case(
    benchmark_id='tsplib_gr96',
    instance='gr96',
    tier='smoke',
    nodes=96,
    raw_path=RAW_DIR / 'gr96.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/gr96.tsp.gz',
    objective=55209,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/gr96.tsp',),
)

GR120 = make_tsp_case(
    benchmark_id='tsplib_gr120',
    instance='gr120',
    tier='calibration',
    nodes=120,
    raw_path=RAW_DIR / 'gr120.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/gr120.tsp.gz',
    objective=6942,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/gr120.tsp',),
)

GR137 = make_tsp_case(
    benchmark_id='tsplib_gr137',
    instance='gr137',
    tier='calibration',
    nodes=137,
    raw_path=RAW_DIR / 'gr137.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/gr137.tsp.gz',
    objective=69853,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/gr137.tsp',),
)

GR202 = make_tsp_case(
    benchmark_id='tsplib_gr202',
    instance='gr202',
    tier='calibration',
    nodes=202,
    raw_path=RAW_DIR / 'gr202.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/gr202.tsp.gz',
    objective=40160,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/gr202.tsp',),
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

CASES = (GR17, GR21, GR24, GR48, GR96, GR120, GR137, GR202, GR431, GR666,)
