from __future__ import annotations

from benchmarks.cases.qaplib.quadratic_assignment._domain import (
    make_qap_case,
    RAW_DIR,
)

CASE_MODULE = __name__

SKO64 = make_qap_case(
    benchmark_id='qaplib_sko64',
    instance='sko64',
    tier='full',
    size=64,
    raw_path=RAW_DIR / 'sko64.dat',
    solution_raw_path=RAW_DIR / 'sko64.sln',
    objective=48498,
    source_label='Sko64',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/sko64.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/sko64.sln',
)

SKO100A = make_qap_case(
    benchmark_id='qaplib_sko100a',
    instance='sko100a',
    tier='pressure',
    size=100,
    raw_path=RAW_DIR / 'sko100a.dat',
    solution_raw_path=RAW_DIR / 'sko100a.sln',
    objective=152002,
    source_label='Sko100a',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/sko100a.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/sko100a.sln',
)

SKO100E = make_qap_case(
    benchmark_id='qaplib_sko100e',
    instance='sko100e',
    tier='pressure',
    size=100,
    raw_path=RAW_DIR / 'sko100e.dat',
    solution_raw_path=RAW_DIR / 'sko100e.sln',
    objective=149150,
    source_label='Sko100e',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/sko100e.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/sko100e.sln',
)

CASES = (SKO64, SKO100A, SKO100E,)
