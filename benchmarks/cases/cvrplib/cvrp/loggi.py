from __future__ import annotations

from benchmarks.cases.cvrplib.cvrp._domain import RAW_DIR, make_cvrp_case

CASE_MODULE = __name__


def _case(name: str, tier: str, nodes: int, customers: int, vehicles: int, capacity: int, arcs: int, objective: int):
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


LOGGI_N401_K23 = _case("Loggi-n401-k23", "full", 401, 400, 23, 100, 160400, 336903)
LOGGI_N501_K24 = _case("Loggi-n501-k24", "pressure", 501, 500, 24, 120, 250500, 177078)
LOGGI_N601_K19 = _case("Loggi-n601-k19", "pressure", 601, 600, 19, 180, 360600, 113155)
LOGGI_N601_K42 = _case("Loggi-n601-k42", "pressure", 601, 600, 42, 80, 360600, 347046)

CASES = (LOGGI_N401_K23, LOGGI_N501_K24, LOGGI_N601_K19, LOGGI_N601_K42)
