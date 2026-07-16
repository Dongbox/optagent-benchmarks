from __future__ import annotations

from benchmarks.cases.qaplib.quadratic_assignment._domain import (
    make_qap_case,
    RAW_DIR,
)

CASE_MODULE = __name__

ROU12 = make_qap_case(
    benchmark_id='qaplib_rou12',
    instance='rou12',
    tier='smoke',
    size=12,
    raw_path=RAW_DIR / 'rou12.dat',
    solution_raw_path=RAW_DIR / 'rou12.sln',
    objective=235528,
    source_label='Rou12',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/rou12.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/rou12.sln',
)

ROU15 = make_qap_case(
    benchmark_id='qaplib_rou15',
    instance='rou15',
    tier='smoke',
    size=15,
    raw_path=RAW_DIR / 'rou15.dat',
    solution_raw_path=RAW_DIR / 'rou15.sln',
    objective=354210,
    source_label='Rou15',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/rou15.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/rou15.sln',
)

ROU20 = make_qap_case(
    benchmark_id='qaplib_rou20',
    instance='rou20',
    tier='calibration',
    size=20,
    raw_path=RAW_DIR / 'rou20.dat',
    solution_raw_path=RAW_DIR / 'rou20.sln',
    objective=725522,
    source_label='Rou20',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/rou20.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/rou20.sln',
)

CASES = (ROU12, ROU15, ROU20,)
