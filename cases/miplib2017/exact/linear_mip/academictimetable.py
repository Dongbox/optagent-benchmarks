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

ACADEMICTIMETABLESMALL = make_mip_case(
    benchmark_id='miplib2017_academictimetablesmall',
    instance='academictimetablesmall',
    tier='full',
    size={'binaries': 28926, 'constraints': 23294, 'continuous': 0, 'integers': 0, 'nonzeros': 268350, 'variables': 28926},
    raw_path=RAW_DIR / 'academictimetablesmall.mps.gz',
    objective=0.0,
    miplib_status='easy',
    tags=('benchmark', 'binary', 'decomposition', 'benchmark_suitable', 'aggregations', 'precedence', 'variable_bound', 'set_partitioning', 'set_packing', 'cardinality', 'invariant_knapsack', 'equation_knapsack', 'binpacking', 'knapsack'),
    case_module=CASE_MODULE,
)

CASES = (ACADEMICTIMETABLESMALL,)
