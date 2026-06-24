from __future__ import annotations

from benchmarks.cases.qaplib.quadratic_assignment._domain import (
    make_qap_case,
    RAW_DIR,
)

CASE_MODULE = __name__

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

CASES = (HAD20,)
