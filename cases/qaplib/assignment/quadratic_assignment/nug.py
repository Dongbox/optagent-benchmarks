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

NUG12 = make_qap_case(
    benchmark_id='qaplib_nug12',
    instance='nug12',
    tier='smoke',
    size=12,
    raw_path=RAW_DIR / 'nug12.dat',
    solution_raw_path=RAW_DIR / 'nug12.sln',
    objective=578,
    source_label='Nug12',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/nug12.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/nug12.sln',
)

NUG20 = make_qap_case(
    benchmark_id='qaplib_nug20',
    instance='nug20',
    tier='calibration',
    size=20,
    raw_path=RAW_DIR / 'nug20.dat',
    solution_raw_path=RAW_DIR / 'nug20.sln',
    objective=2570,
    source_label='Nug20',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/nug20.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/nug20.sln',
)

CASES = (NUG12, NUG20)
