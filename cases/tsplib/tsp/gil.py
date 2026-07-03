from __future__ import annotations

from benchmarks.cases.tsplib.tsp._domain import (
    make_tsp_case,
    RAW_DIR,
)

CASE_MODULE = __name__

GIL262 = make_tsp_case(
    benchmark_id='tsplib_gil262',
    instance='gil262',
    tier='calibration',
    nodes=262,
    raw_path=RAW_DIR / 'gil262.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/gil262.tsp.gz',
    objective=2378,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/gil262.tsp',),
)

CASES = (GIL262,)
