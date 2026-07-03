from __future__ import annotations

from benchmarks.cases.qaplib.quadratic_assignment._domain import (
    make_qap_case,
    RAW_DIR,
)

CASE_MODULE = __name__

STE36C = make_qap_case(
    benchmark_id='qaplib_ste36c',
    instance='ste36c',
    tier='full',
    size=36,
    raw_path=RAW_DIR / 'ste36c.dat',
    solution_raw_path=RAW_DIR / 'ste36c.sln',
    objective=8239110,
    source_label='Ste36c',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/ste36c.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/ste36c.sln',
)

CASES = (STE36C,)
