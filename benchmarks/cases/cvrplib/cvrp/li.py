from __future__ import annotations

from benchmarks.cases.cvrplib.cvrp._domain import RAW_DIR, make_cvrp_case

CASE_MODULE = __name__


LI_21 = make_cvrp_case(benchmark_id="cvrplib_li_21", instance="li_21", source_instance="Li_21", tier="pressure", nodes=561, customers=560, vehicles=10, capacity=1200, directed_arcs=314160, raw_path=RAW_DIR / "Li_21.json", objective=16212.82548, case_module=CASE_MODULE)

CASES = (LI_21,)
