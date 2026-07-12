from __future__ import annotations

from benchmarks.cases.miplib2017.linear_mip._domain import (
    make_mip_case,
    RAW_DIR,
)

CASE_MODULE = __name__

FAST0507 = make_mip_case(
    benchmark_id='miplib2017_fast0507',
    instance='fast0507',
    tier='full',
    size={'binaries': 63009, 'constraints': 507, 'continuous': 0, 'integers': 0, 'nonzeros': 409349, 'variables': 63009},
    raw_path=RAW_DIR / 'fast0507.mps.gz',
    objective=174.0,
    miplib_status='easy',
    tags=('benchmark', 'binary', 'benchmark_suitable', 'variable_bound', 'set_covering'),
    case_module=CASE_MODULE,
)

CASES = (FAST0507,)
