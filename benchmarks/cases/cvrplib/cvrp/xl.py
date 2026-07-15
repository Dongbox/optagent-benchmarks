from __future__ import annotations

from benchmarks.cases.cvrplib.cvrp._domain import RAW_DIR, make_cvrp_case

CASE_MODULE = __name__


XL_N1094_K157 = make_cvrp_case(benchmark_id="cvrplib_xl_n1094_k157", instance="xl-n1094-k157", source_instance="XL-n1094-k157", tier="pressure", nodes=1094, customers=1093, vehicles=157, capacity=7, directed_arcs=1195742, raw_path=RAW_DIR / "XL-n1094-k157.json", objective=112431, case_module=CASE_MODULE)

CASES = (XL_N1094_K157,)
