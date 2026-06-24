from __future__ import annotations

from benchmarks.cases.qaplib.assignment.quadratic_assignment._common import (
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

CHR12A = make_qap_case(
    benchmark_id='qaplib_chr12a',
    instance='chr12a',
    tier='smoke',
    size=12,
    raw_path=RAW_DIR / 'chr12a.dat',
    solution_raw_path=RAW_DIR / 'chr12a.sln',
    objective=9552,
    source_label='Chr12a',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/chr12a.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/chr12a.sln',
)

CASES = (CHR12A,)
