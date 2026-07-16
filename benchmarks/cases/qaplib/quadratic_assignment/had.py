from __future__ import annotations

from benchmarks.cases.qaplib.quadratic_assignment._domain import (
    make_qap_case,
    RAW_DIR,
)

CASE_MODULE = __name__

HAD12 = make_qap_case(
    benchmark_id='qaplib_had12',
    instance='had12',
    tier='smoke',
    size=12,
    raw_path=RAW_DIR / 'had12.dat',
    solution_raw_path=RAW_DIR / 'had12.sln',
    objective=1652,
    source_label='Had12',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/had12.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/had12.sln',
)

HAD16 = make_qap_case(
    benchmark_id='qaplib_had16',
    instance='had16',
    tier='smoke',
    size=16,
    raw_path=RAW_DIR / 'had16.dat',
    solution_raw_path=RAW_DIR / 'had16.sln',
    objective=3720,
    source_label='Had16',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/had16.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/had16.sln',
)

HAD20 = make_qap_case(
    benchmark_id='qaplib_had20',
    instance='had20',
    tier='calibration',
    size=20,
    raw_path=RAW_DIR / 'had20.dat',
    solution_raw_path=RAW_DIR / 'had20.sln',
    objective=6922,
    source_label='Had20',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/had20.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/had20.sln',
)

CASES = (HAD12, HAD16, HAD20,)
