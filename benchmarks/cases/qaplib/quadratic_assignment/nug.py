from __future__ import annotations

from benchmarks.cases.qaplib.quadratic_assignment._domain import (
    make_qap_case,
    RAW_DIR,
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

NUG14 = make_qap_case(
    benchmark_id='qaplib_nug14',
    instance='nug14',
    tier='smoke',
    size=14,
    raw_path=RAW_DIR / 'nug14.dat',
    solution_raw_path=RAW_DIR / 'nug14.sln',
    objective=1014,
    source_label='Nug14',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/nug14.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/nug14.sln',
)

NUG16A = make_qap_case(
    benchmark_id='qaplib_nug16a',
    instance='nug16a',
    tier='smoke',
    size=16,
    raw_path=RAW_DIR / 'nug16a.dat',
    solution_raw_path=RAW_DIR / 'nug16a.sln',
    objective=1610,
    source_label='Nug16a',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/nug16a.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/nug16a.sln',
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

NUG28 = make_qap_case(
    benchmark_id='qaplib_nug28',
    instance='nug28',
    tier='calibration',
    size=28,
    raw_path=RAW_DIR / 'nug28.dat',
    solution_raw_path=RAW_DIR / 'nug28.sln',
    objective=5166,
    source_label='Nug28',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/nug28.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/nug28.sln',
)

NUG30 = make_qap_case(
    benchmark_id='qaplib_nug30',
    instance='nug30',
    tier='calibration',
    size=30,
    raw_path=RAW_DIR / 'nug30.dat',
    solution_raw_path=RAW_DIR / 'nug30.sln',
    objective=6124,
    source_label='Nug30',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/nug30.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/nug30.sln',
)

CASES = (NUG12, NUG14, NUG16A, NUG20, NUG28, NUG30,)
