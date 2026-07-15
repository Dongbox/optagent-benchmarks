from __future__ import annotations

from benchmarks.cases.cvrplib.cvrp._domain import RAW_DIR, make_cvrp_case

CASE_MODULE = __name__


def _case(name: str, tier: str, nodes: int, customers: int, vehicles: int, capacity: int, arcs: int, objective: int | float):
    instance = name.lower()
    return make_cvrp_case(
        benchmark_id=f"cvrplib_{instance.replace('-', '_')}",
        instance=instance,
        source_instance=name,
        tier=tier,
        nodes=nodes,
        customers=customers,
        vehicles=vehicles,
        capacity=capacity,
        directed_arcs=arcs,
        raw_path=RAW_DIR / f"{name}.json",
        objective=objective,
        case_module=CASE_MODULE,
    )


B_N31_K5 = _case("B-n31-k5", "smoke", 31, 30, 5, 100, 930, 672)
B_N34_K5 = _case("B-n34-k5", "smoke", 34, 33, 5, 100, 1122, 788)
B_N38_K6 = _case("B-n38-k6", "smoke", 38, 37, 6, 100, 1406, 805)
B_N45_K5 = _case("B-n45-k5", "smoke", 45, 44, 5, 100, 1980, 751)
B_N56_K7 = _case("B-n56-k7", "smoke", 56, 55, 7, 100, 3080, 707)

CASES = (B_N31_K5, B_N34_K5, B_N38_K6, B_N45_K5, B_N56_K7)
