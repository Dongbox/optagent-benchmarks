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


ORTEC_N242_K12 = _case("ORTEC-n242-k12", "full", 242, 241, 12, 125, 58322, 123750)
ORTEC_N455_K41 = _case("ORTEC-n455-k41", "full", 455, 454, 41, 70, 206570, 292485)
ORTEC_N510_K23 = _case("ORTEC-n510-k23", "pressure", 510, 509, 23, 145, 259590, 184529)
ORTEC_N701_K64 = _case("ORTEC-n701-k64", "pressure", 701, 700, 64, 80, 490700, 445541)

CASES = (ORTEC_N242_K12, ORTEC_N455_K41, ORTEC_N510_K23, ORTEC_N701_K64)
