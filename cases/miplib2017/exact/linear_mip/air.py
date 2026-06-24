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

AIR05 = make_mip_case(
    benchmark_id='miplib2017_air05',
    instance='air05',
    tier='calibration',
    size={'binaries': 7195, 'constraints': 426, 'continuous': 0, 'integers': 0, 'nonzeros': 52121, 'variables': 7195},
    raw_path=RAW_DIR / 'air05.mps.gz',
    objective=26374.0,
    miplib_status='easy',
    tags=('benchmark', 'binary', 'benchmark_suitable', 'set_partitioning'),
    case_module=CASE_MODULE,
)

CASES = (AIR05,)
