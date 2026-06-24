from __future__ import annotations

from benchmarks.cases.tsplib.tsp._common import (
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

BERLIN52 = make_tsp_case(
    benchmark_id='tsplib_berlin52',
    instance='berlin52',
    tier='smoke',
    nodes=52,
    raw_path=RAW_DIR / 'berlin52.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/berlin52.tsp.gz',
    objective=7542,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/berlin52.tsp',),
)

CASES = (BERLIN52,)
