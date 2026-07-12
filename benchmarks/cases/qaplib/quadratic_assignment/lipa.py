from __future__ import annotations

from benchmarks.cases.qaplib.quadratic_assignment._domain import (
    make_qap_case,
    RAW_DIR,
)

CASE_MODULE = __name__

LIPA40B = make_qap_case(
    benchmark_id='qaplib_lipa40b',
    instance='lipa40b',
    tier='full',
    size=40,
    raw_path=RAW_DIR / 'lipa40b.dat',
    solution_raw_path=RAW_DIR / 'lipa40b.sln',
    objective=476581,
    source_label='Lipa40b',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/lipa40b.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/lipa40b.sln',
)

LIPA90A = make_qap_case(
    benchmark_id='qaplib_lipa90a',
    instance='lipa90a',
    tier='pressure',
    size=90,
    raw_path=RAW_DIR / 'lipa90a.dat',
    solution_raw_path=RAW_DIR / 'lipa90a.sln',
    objective=360630,
    source_label='Lipa90a',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/lipa90a.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/lipa90a.sln',
)

LIPA90B = make_qap_case(
    benchmark_id='qaplib_lipa90b',
    instance='lipa90b',
    tier='pressure',
    size=90,
    raw_path=RAW_DIR / 'lipa90b.dat',
    solution_raw_path=RAW_DIR / 'lipa90b.sln',
    objective=12490441,
    source_label='Lipa90b',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/lipa90b.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/lipa90b.sln',
)

LIPA20A = make_qap_case(
    benchmark_id='qaplib_lipa20a',
    instance='lipa20a',
    tier='calibration',
    size=20,
    raw_path=RAW_DIR / 'lipa20a.dat',
    solution_raw_path=RAW_DIR / 'lipa20a.sln',
    objective=3683,
    source_label='Lipa20a',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/lipa20a.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/lipa20a.sln',
)

LIPA20B = make_qap_case(
    benchmark_id='qaplib_lipa20b',
    instance='lipa20b',
    tier='calibration',
    size=20,
    raw_path=RAW_DIR / 'lipa20b.dat',
    solution_raw_path=RAW_DIR / 'lipa20b.sln',
    objective=27076,
    source_label='Lipa20b',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/lipa20b.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/lipa20b.sln',
)

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

CASES = (LIPA40B, LIPA90A, LIPA90B, LIPA20A, LIPA20B, LIPA40A,)
