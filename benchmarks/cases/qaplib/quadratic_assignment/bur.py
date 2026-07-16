from __future__ import annotations

from benchmarks.cases.qaplib.quadratic_assignment._domain import (
    make_qap_case,
    RAW_DIR,
)

CASE_MODULE = __name__

BUR26A = make_qap_case(
    benchmark_id='qaplib_bur26a',
    instance='bur26a',
    tier='calibration',
    size=26,
    raw_path=RAW_DIR / 'bur26a.dat',
    solution_raw_path=RAW_DIR / 'bur26a.sln',
    objective=5426670,
    source_label='Bur26a',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/bur26a.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/bur26a.sln',
)

CASES = (BUR26A,)
