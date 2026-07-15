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


A_N32_K5 = _case("A-n32-k5", "smoke", 32, 31, 5, 100, 992, 784)

CASES = (A_N32_K5,)
