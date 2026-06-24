from __future__ import annotations

from benchmarks.cases.miplib2017.exact.linear_mip._common import (
    make_mip_case,
    RAW_DIR,
    SOURCE,
    SOURCE_KEY,
    PROBLEM_TYPE,
    INSTANCE_TYPE,
    FAMILY,
    MODEL_STYLE,
)

CASE_MODULE = __name__

REBLOCK115 = make_mip_case(
    benchmark_id='miplib2017_reblock115',
    instance='reblock115',
    tier='calibration',
    size={'binaries': 1150, 'constraints': 4735, 'continuous': 0, 'integers': 0, 'nonzeros': 13724, 'variables': 1150},
    raw_path=RAW_DIR / 'reblock115.mps.gz',
    objective=-36800603.2332,
    miplib_status='easy',
    tags=('benchmark', 'binary', 'benchmark_suitable', 'precedence', 'knapsack'),
    case_module=CASE_MODULE,
)

CASES = (REBLOCK115,)
