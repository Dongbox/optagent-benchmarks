from __future__ import annotations

from benchmarks.cases.qaplib.quadratic_assignment._domain import (
    make_qap_case,
    RAW_DIR,
)

CASE_MODULE = __name__

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

CHR15A = make_qap_case(
    benchmark_id='qaplib_chr15a',
    instance='chr15a',
    tier='smoke',
    size=15,
    raw_path=RAW_DIR / 'chr15a.dat',
    solution_raw_path=RAW_DIR / 'chr15a.sln',
    objective=9896,
    source_label='Chr15a',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/chr15a.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/chr15a.sln',
)

CHR20B = make_qap_case(
    benchmark_id='qaplib_chr20b',
    instance='chr20b',
    tier='calibration',
    size=20,
    raw_path=RAW_DIR / 'chr20b.dat',
    solution_raw_path=RAW_DIR / 'chr20b.sln',
    objective=2298,
    source_label='Chr20b',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/chr20b.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/chr20b.sln',
)

CHR20C = make_qap_case(
    benchmark_id='qaplib_chr20c',
    instance='chr20c',
    tier='calibration',
    size=20,
    raw_path=RAW_DIR / 'chr20c.dat',
    solution_raw_path=RAW_DIR / 'chr20c.sln',
    objective=14142,
    source_label='Chr20c',
    case_module=CASE_MODULE,
    instance_url='https://qaplib.mgi.polymtl.ca/data.d/chr20c.dat',
    solution_url='https://qaplib.mgi.polymtl.ca/soln.d/chr20c.sln',
)

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

CASES = (CHR12A, CHR15A, CHR20B, CHR20C, CHR25A,)
