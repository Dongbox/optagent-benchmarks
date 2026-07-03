from __future__ import annotations

from benchmarks.cases.tsplib.tsp._domain import (
    make_tsp_case,
    RAW_DIR,
)

CASE_MODULE = __name__

PCB442 = make_tsp_case(
    benchmark_id='tsplib_pcb442',
    instance='pcb442',
    tier='calibration',
    nodes=442,
    raw_path=RAW_DIR / 'pcb442.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/pcb442.tsp.gz',
    objective=50778,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/pcb442.tsp',),
)

PCB1173 = make_tsp_case(
    benchmark_id='tsplib_pcb1173',
    instance='pcb1173',
    tier='pressure',
    nodes=1173,
    raw_path=RAW_DIR / 'pcb1173.tsp',
    instance_url='https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/pcb1173.tsp.gz',
    objective=56892,
    case_module=CASE_MODULE,
    mirror_urls=('https://raw.githubusercontent.com/mastqe/tsplib/master/pcb1173.tsp',),
)

CASES = (PCB442, PCB1173)
