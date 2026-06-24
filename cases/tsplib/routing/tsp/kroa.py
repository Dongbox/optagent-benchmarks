from __future__ import annotations

from benchmarks.cases.tsplib.routing.tsp._common import (
    make_tsp_case,
    RAW_DIR,
    SOURCE,
    SOURCE_KEY,
    PROBLEM_TYPE,
    INSTANCE_TYPE,
    FAMILY,
    MODEL_STYLE,
    BLACKBOX_TSP_MODEL_STYLE,
    GRAPH_TSP_MODEL_STYLE,
    DEFAULT_TSP_MODEL_STYLES,
    SUPPORTED_TSP_MODEL_STYLES,
)

CASE_MODULE = __name__

KROA100 = make_tsp_case(
    benchmark_id='tsplib_kroa100',
    instance='kroa100',
    tier='calibration',
    nodes=100,
    raw_path=RAW_DIR / 'kroa100.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/kroA100.tsp.gz',
    objective=21282,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/kroA100.tsp',),
)

CASES = (KROA100,)
