from __future__ import annotations

from benchmarks.cases.miplib2017.linear_mip._domain import (
    make_mip_case,
    RAW_DIR,
)

CASE_MODULE = __name__

CASE_50V_10 = make_mip_case(
    benchmark_id='miplib2017_50v-10',
    instance='50v-10',
    tier='smoke',
    size={'binaries': 1464, 'constraints': 233, 'continuous': 366, 'integers': 183, 'nonzeros': 2745, 'variables': 2013},
    raw_path=RAW_DIR / '50v-10.mps.gz',
    objective=3311.1799841,
    miplib_status='easy',
    tags=('benchmark', 'decomposition', 'benchmark_suitable', 'mixed_binary', 'general_linear'),
    case_module=CASE_MODULE,
)

CASES = (CASE_50V_10,)
