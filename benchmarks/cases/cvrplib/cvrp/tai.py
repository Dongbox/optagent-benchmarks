from __future__ import annotations

from benchmarks.cases.cvrplib.cvrp._domain import RAW_DIR, make_cvrp_case

CASE_MODULE = __name__


def _case(name: str, tier: str, nodes: int, customers: int, vehicles: int, capacity: int, arcs: int, objective: float):
    instance = name.lower()
    return make_cvrp_case(
        benchmark_id=f"cvrplib_{instance}",
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


TAI75A = _case("Tai75a", "smoke", 76, 75, 10, 1445, 5700, 1618.36)
TAI75B = _case("Tai75b", "smoke", 76, 75, 10, 1679, 5700, 1344.62)
TAI100C = _case("Tai100c", "calibration", 101, 100, 11, 2043, 10100, 1406.2)
TAI150C = _case("Tai150c", "calibration", 151, 150, 15, 2021, 22650, 2358.66)
TAI385 = _case("Tai385", "full", 386, 385, 47, 65, 148610, 24366.41339)

CASES = (TAI75A, TAI75B, TAI100C, TAI150C, TAI385)
