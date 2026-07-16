from __future__ import annotations

from benchmarks.cases.qaplib.quadratic_assignment._domain import (
    make_qap_case,
    RAW_DIR,
)

CASE_MODULE = __name__

ELS19 = make_qap_case(
    benchmark_id='qaplib_els19',
    instance='els19',
    tier='calibration',
    size=19,
    raw_path=RAW_DIR / 'els19.dat',
    solution_raw_path=RAW_DIR / 'els19.sln',
    objective=17212548,
    source_label='Els19',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/els19.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/els19.sln',
)

CASES = (ELS19,)
