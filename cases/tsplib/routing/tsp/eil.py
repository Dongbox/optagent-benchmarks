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

EIL51 = make_tsp_case(
    benchmark_id='tsplib_eil51',
    instance='eil51',
    tier='smoke',
    nodes=51,
    raw_path=RAW_DIR / 'eil51.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/eil51.tsp.gz',
    objective=426,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/eil51.tsp',),
)

CASES = (EIL51,)
