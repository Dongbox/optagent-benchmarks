from __future__ import annotations

from benchmarks.cases.qaplib.quadratic_assignment._common import (
    make_qap_case,
    RAW_DIR,
    SOURCE,
    SOURCE_KEY,
    PROBLEM_TYPE,
    INSTANCE_TYPE,
    FAMILY,
    MODEL_STYLE,
)

CASE_MODULE = __name__

LIPA40A = make_qap_case(
    benchmark_id='qaplib_lipa40a',
    instance='lipa40a',
    tier='full',
    size=40,
    raw_path=RAW_DIR / 'lipa40a.dat',
    solution_raw_path=RAW_DIR / 'lipa40a.sln',
    objective=31538,
    source_label='Lipa40a',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/lipa40a.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/lipa40a.sln',
)

CASES = (LIPA40A,)
