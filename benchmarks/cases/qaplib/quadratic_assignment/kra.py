from __future__ import annotations

from benchmarks.cases.qaplib.quadratic_assignment._domain import (
    make_qap_case,
    RAW_DIR,
)

CASE_MODULE = __name__

KRA30A = make_qap_case(
    benchmark_id='qaplib_kra30a',
    instance='kra30a',
    tier='calibration',
    size=30,
    raw_path=RAW_DIR / 'kra30a.dat',
    solution_raw_path=RAW_DIR / 'kra30a.sln',
    objective=88900,
    source_label='Kra30a',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/kra30a.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/kra30a.sln',
)

KRA32 = make_qap_case(
    benchmark_id='qaplib_kra32',
    instance='kra32',
    tier='full',
    size=32,
    raw_path=RAW_DIR / 'kra32.dat',
    solution_raw_path=RAW_DIR / 'kra32.sln',
    objective=88700,
    source_label='Kra32',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/kra32.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/kra32.sln',
)

CASES = (KRA30A, KRA32,)
