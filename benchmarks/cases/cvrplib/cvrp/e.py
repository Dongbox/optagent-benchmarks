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


E_N22_K4 = _case("E-n22-k4", "smoke", 22, 21, 4, 6000, 462, 375)
E_N23_K3 = _case("E-n23-k3", "smoke", 23, 22, 3, 4500, 506, 569)
E_N31_K7 = _case("E-n31-k7", "smoke", 31, 30, 7, 140, 930, 379)
E_N101_K14 = _case("E-n101-k14", "calibration", 101, 100, 14, 112, 10100, 1067)

CASES = (E_N22_K4, E_N23_K3, E_N31_K7, E_N101_K14)
