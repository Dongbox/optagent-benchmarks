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


P_N16_K8 = _case("P-n16-k8", "smoke", 16, 15, 8, 35, 240, 450)
P_N19_K2 = _case("P-n19-k2", "smoke", 19, 18, 2, 160, 342, 212)
P_N55_K15 = _case("P-n55-k15", "smoke", 55, 54, 15, 70, 2970, 989)
P_N76_K4 = _case("P-n76-k4", "smoke", 76, 75, 4, 350, 5700, 593)

CASES = (P_N16_K8, P_N19_K2, P_N55_K15, P_N76_K4)
