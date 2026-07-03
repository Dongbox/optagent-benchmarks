from __future__ import annotations

from benchmarks.cases.qaplib.quadratic_assignment._domain import (
    make_qap_case,
    RAW_DIR,
)

CASE_MODULE = __name__

CHR25A = make_qap_case(
    benchmark_id='qaplib_chr25a',
    instance='chr25a',
    tier='calibration',
    size=25,
    raw_path=RAW_DIR / 'chr25a.dat',
    solution_raw_path=RAW_DIR / 'chr25a.sln',
    objective=3796,
    source_label='Chr25a',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/chr25a.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/chr25a.sln',
)

CHR12A = make_qap_case(
    benchmark_id='qaplib_chr12a',
    instance='chr12a',
    tier='smoke',
    size=12,
    raw_path=RAW_DIR / 'chr12a.dat',
    solution_raw_path=RAW_DIR / 'chr12a.sln',
    objective=9552,
    source_label='Chr12a',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/chr12a.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/chr12a.sln',
)

CASES = (CHR25A, CHR12A,)
