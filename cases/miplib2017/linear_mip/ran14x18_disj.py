from __future__ import annotations

from benchmarks.cases.miplib2017.linear_mip._common import (
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

RAN14X18_DISJ_8 = make_mip_case(
    benchmark_id='miplib2017_ran14x18-disj-8',
    instance='ran14x18-disj-8',
    tier='smoke',
    size={'binaries': 252, 'constraints': 447, 'continuous': 252, 'integers': 0, 'nonzeros': 10277, 'variables': 504},
    raw_path=RAW_DIR / 'ran14x18-disj-8.mps.gz',
    objective=3712.0,
    miplib_status='easy',
    tags=('benchmark', 'benchmark_suitable', 'variable_bound', 'set_covering', 'mixed_binary'),
    case_module=CASE_MODULE,
)

CASES = (RAN14X18_DISJ_8,)
