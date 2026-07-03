from __future__ import annotations

from benchmarks.cases.qaplib.quadratic_assignment._domain import (
    make_qap_case,
    RAW_DIR,
)

CASE_MODULE = __name__

THO150 = make_qap_case(
    benchmark_id='qaplib_tho150',
    instance='tho150',
    tier='pressure',
    size=150,
    raw_path=RAW_DIR / 'tho150.dat',
    solution_raw_path=RAW_DIR / 'tho150.sln',
    objective=8133398,
    source_label='Tho150',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/tho150.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/tho150.sln',
)

THO40 = make_qap_case(
    benchmark_id='qaplib_tho40',
    instance='tho40',
    tier='full',
    size=40,
    raw_path=RAW_DIR / 'tho40.dat',
    solution_raw_path=RAW_DIR / 'tho40.sln',
    objective=240516,
    source_label='Tho40',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/tho40.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/tho40.sln',
)

THO30 = make_qap_case(
    benchmark_id='qaplib_tho30',
    instance='tho30',
    tier='calibration',
    size=30,
    raw_path=RAW_DIR / 'tho30.dat',
    solution_raw_path=RAW_DIR / 'tho30.sln',
    objective=149936,
    source_label='Tho30',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/tho30.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/tho30.sln',
)

CASES = (THO150, THO40, THO30,)
