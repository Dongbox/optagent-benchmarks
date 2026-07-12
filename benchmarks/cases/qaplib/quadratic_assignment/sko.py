from __future__ import annotations

from benchmarks.cases.qaplib.quadratic_assignment._domain import (
    make_qap_case,
    RAW_DIR,
)

CASE_MODULE = __name__

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

SKO42 = make_qap_case(
    benchmark_id='qaplib_sko42',
    instance='sko42',
    tier='full',
    size=42,
    raw_path=RAW_DIR / 'sko42.dat',
    solution_raw_path=RAW_DIR / 'sko42.sln',
    objective=15812,
    source_label='Sko42',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/sko42.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/sko42.sln',
)

CASES = (SKO100A, SKO64, SKO42,)
