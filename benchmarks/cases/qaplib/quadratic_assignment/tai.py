from __future__ import annotations

from benchmarks.cases.qaplib.quadratic_assignment._domain import (
    make_qap_case,
    RAW_DIR,
)

CASE_MODULE = __name__

TAI64C = make_qap_case(
    benchmark_id='qaplib_tai64c',
    instance='tai64c',
    tier='full',
    size=64,
    raw_path=RAW_DIR / 'tai64c.dat',
    solution_raw_path=RAW_DIR / 'tai64c.sln',
    objective=1855928,
    source_label='Tai64c',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/tai64c.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/tai64c.sln',
)

TAI50B = make_qap_case(
    benchmark_id='qaplib_tai50b',
    instance='tai50b',
    tier='full',
    size=50,
    raw_path=RAW_DIR / 'tai50b.dat',
    solution_raw_path=RAW_DIR / 'tai50b.sln',
    objective=458821517,
    source_label='Tai50b',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/tai50b.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/tai50b.sln',
)

TAI80B = make_qap_case(
    benchmark_id='qaplib_tai80b',
    instance='tai80b',
    tier='full',
    size=80,
    raw_path=RAW_DIR / 'tai80b.dat',
    solution_raw_path=RAW_DIR / 'tai80b.sln',
    objective=818415043,
    source_label='Tai80b',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/tai80b.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/tai80b.sln',
)

TAI100B = make_qap_case(
    benchmark_id='qaplib_tai100b',
    instance='tai100b',
    tier='pressure',
    size=100,
    raw_path=RAW_DIR / 'tai100b.dat',
    solution_raw_path=RAW_DIR / 'tai100b.sln',
    objective=1185996137,
    source_label='Tai100b',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/tai100b.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/tai100b.sln',
)

TAI100A = make_qap_case(
    benchmark_id='qaplib_tai100a',
    instance='tai100a',
    tier='pressure',
    size=100,
    raw_path=RAW_DIR / 'tai100a.dat',
    solution_raw_path=RAW_DIR / 'tai100a.sln',
    objective=21052466,
    source_label='Tai100a',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/tai100a.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/tai100a.sln',
)

TAI35B = make_qap_case(
    benchmark_id='qaplib_tai35b',
    instance='tai35b',
    tier='full',
    size=35,
    raw_path=RAW_DIR / 'tai35b.dat',
    solution_raw_path=RAW_DIR / 'tai35b.sln',
    objective=283315445,
    source_label='Tai35b',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/tai35b.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/tai35b.sln',
)

TAI20B = make_qap_case(
    benchmark_id='qaplib_tai20b',
    instance='tai20b',
    tier='calibration',
    size=20,
    raw_path=RAW_DIR / 'tai20b.dat',
    solution_raw_path=RAW_DIR / 'tai20b.sln',
    objective=122455319,
    source_label='Tai20b',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/tai20b.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/tai20b.sln',
)

TAI12B = make_qap_case(
    benchmark_id='qaplib_tai12b',
    instance='tai12b',
    tier='smoke',
    size=12,
    raw_path=RAW_DIR / 'tai12b.dat',
    solution_raw_path=RAW_DIR / 'tai12b.sln',
    objective=39464925,
    source_label='Tai12b',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/tai12b.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/tai12b.sln',
)

TAI30A = make_qap_case(
    benchmark_id='qaplib_tai30a',
    instance='tai30a',
    tier='calibration',
    size=30,
    raw_path=RAW_DIR / 'tai30a.dat',
    solution_raw_path=RAW_DIR / 'tai30a.sln',
    objective=1818146,
    source_label='Tai30a',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/tai30a.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/tai30a.sln',
)

TAI35A = make_qap_case(
    benchmark_id='qaplib_tai35a',
    instance='tai35a',
    tier='full',
    size=35,
    raw_path=RAW_DIR / 'tai35a.dat',
    solution_raw_path=RAW_DIR / 'tai35a.sln',
    objective=2422002,
    source_label='Tai35a',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/tai35a.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/tai35a.sln',
)

TAI30B = make_qap_case(
    benchmark_id='qaplib_tai30b',
    instance='tai30b',
    tier='calibration',
    size=30,
    raw_path=RAW_DIR / 'tai30b.dat',
    solution_raw_path=RAW_DIR / 'tai30b.sln',
    objective=637117113,
    source_label='Tai30b',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/tai30b.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/tai30b.sln',
)

CASES = (TAI64C, TAI50B, TAI80B, TAI100B, TAI100A, TAI35B, TAI20B, TAI12B, TAI30A, TAI35A, TAI30B,)
