from __future__ import annotations

from benchmarks.cases.qaplib.quadratic_assignment._domain import (
    make_qap_case,
    RAW_DIR,
)

CASE_MODULE = __name__

ESC32E = make_qap_case(
    benchmark_id='qaplib_esc32e',
    instance='esc32e',
    tier='full',
    size=32,
    raw_path=RAW_DIR / 'esc32e.dat',
    solution_raw_path=RAW_DIR / 'esc32e.sln',
    objective=2,
    source_label='Esc32e',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/esc32e.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/esc32e.sln',
)

ESC128 = make_qap_case(
    benchmark_id='qaplib_esc128',
    instance='esc128',
    tier='pressure',
    size=128,
    raw_path=RAW_DIR / 'esc128.dat',
    solution_raw_path=RAW_DIR / 'esc128.sln',
    objective=64,
    source_label='Esc128',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/esc128.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/esc128.sln',
)

ESC16B = make_qap_case(
    benchmark_id='qaplib_esc16b',
    instance='esc16b',
    tier='smoke',
    size=16,
    raw_path=RAW_DIR / 'esc16b.dat',
    solution_raw_path=RAW_DIR / 'esc16b.sln',
    objective=292,
    source_label='Esc16b',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/esc16b.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/esc16b.sln',
)

ESC16H = make_qap_case(
    benchmark_id='qaplib_esc16h',
    instance='esc16h',
    tier='smoke',
    size=16,
    raw_path=RAW_DIR / 'esc16h.dat',
    solution_raw_path=RAW_DIR / 'esc16h.sln',
    objective=996,
    source_label='Esc16h',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/esc16h.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/esc16h.sln',
)

CASES = (ESC32E, ESC128, ESC16B, ESC16H,)
