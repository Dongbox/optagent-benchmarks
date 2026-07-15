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


GOLDEN_5 = _case("Golden_5", "full", 201, 200, 5, 900, 40200, 6460.98)
GOLDEN_13 = _case("Golden_13", "full", 253, 252, 26, 1000, 63756, 857.189)
GOLDEN_17 = _case("Golden_17", "full", 241, 240, 22, 200, 57840, 707.756)

CASES = (GOLDEN_5, GOLDEN_13, GOLDEN_17)
