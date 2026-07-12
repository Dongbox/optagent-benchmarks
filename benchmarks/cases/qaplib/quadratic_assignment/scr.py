from __future__ import annotations

from benchmarks.cases.qaplib.quadratic_assignment._domain import (
    make_qap_case,
    RAW_DIR,
)

CASE_MODULE = __name__

SCR20 = make_qap_case(
    benchmark_id='qaplib_scr20',
    instance='scr20',
    tier='calibration',
    size=20,
    raw_path=RAW_DIR / 'scr20.dat',
    solution_raw_path=RAW_DIR / 'scr20.sln',
    objective=110030,
    source_label='Scr20',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/scr20.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/scr20.sln',
)

SCR12 = make_qap_case(
    benchmark_id='qaplib_scr12',
    instance='scr12',
    tier='smoke',
    size=12,
    raw_path=RAW_DIR / 'scr12.dat',
    solution_raw_path=RAW_DIR / 'scr12.sln',
    objective=31410,
    source_label='Scr12',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/scr12.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/scr12.sln',
)

CASES = (SCR20, SCR12,)
