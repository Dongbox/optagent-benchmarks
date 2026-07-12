from __future__ import annotations

from benchmarks.cases.qaplib.quadratic_assignment._domain import (
    make_qap_case,
    RAW_DIR,
)

CASE_MODULE = __name__

WIL100 = make_qap_case(
    benchmark_id='qaplib_wil100',
    instance='wil100',
    tier='pressure',
    size=100,
    raw_path=RAW_DIR / 'wil100.dat',
    solution_raw_path=RAW_DIR / 'wil100.sln',
    objective=273038,
    source_label='Wil100',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/wil100.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/wil100.sln',
)

WIL50 = make_qap_case(
    benchmark_id='qaplib_wil50',
    instance='wil50',
    tier='full',
    size=50,
    raw_path=RAW_DIR / 'wil50.dat',
    solution_raw_path=RAW_DIR / 'wil50.sln',
    objective=48816,
    source_label='Wil50',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/wil50.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/wil50.sln',
)

CASES = (WIL100, WIL50,)
