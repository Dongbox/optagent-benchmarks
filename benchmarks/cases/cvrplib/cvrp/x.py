from __future__ import annotations

from benchmarks.cases.cvrplib.cvrp._domain import RAW_DIR, make_cvrp_case

CASE_MODULE = __name__


def _case(name: str, tier: str, nodes: int, customers: int, vehicles: int, capacity: int, arcs: int, objective: int, route_count: int | None = None):
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
        reference_route_count=route_count,
    )


X_N106_K14 = _case("X-n106-k14", "calibration", 106, 105, 14, 600, 11130, 26362)
X_N157_K13 = _case("X-n157-k13", "calibration", 157, 156, 13, 12, 24492, 16876)
X_N172_K51 = _case("X-n172-k51", "calibration", 172, 171, 51, 161, 29412, 45607, 53)
X_N204_K19 = _case("X-n204-k19", "full", 204, 203, 19, 836, 41412, 19565)
X_N219_K73 = _case("X-n219-k73", "full", 219, 218, 73, 3, 47742, 117595)
X_N228_K23 = _case("X-n228-k23", "full", 228, 227, 23, 154, 51756, 25742)
X_N237_K14 = _case("X-n237-k14", "full", 237, 236, 14, 18, 55932, 27042)
X_N280_K17 = _case("X-n280-k17", "full", 280, 279, 17, 192, 78120, 33503)
X_N284_K15 = _case("X-n284-k15", "full", 284, 283, 15, 109, 80372, 20215)
X_N313_K71 = _case("X-n313-k71", "full", 313, 312, 71, 248, 97656, 94043, 72)
X_N317_K53 = _case("X-n317-k53", "full", 317, 316, 53, 6, 100172, 78355)
X_N502_K39 = _case("X-n502-k39", "pressure", 502, 501, 39, 13, 251502, 69226)
X_N524_K153 = _case("X-n524-k153", "pressure", 524, 523, 153, 125, 274052, 154593, 155)
X_N536_K96 = _case("X-n536-k96", "pressure", 536, 535, 96, 371, 286760, 94846)
X_N548_K50 = _case("X-n548-k50", "pressure", 548, 547, 50, 11, 299756, 86700)
X_N573_K30 = _case("X-n573-k30", "pressure", 573, 572, 30, 210, 327756, 50673)
X_N613_K62 = _case("X-n613-k62", "pressure", 613, 612, 62, 523, 375156, 59535)
X_N655_K131 = _case("X-n655-k131", "pressure", 655, 654, 131, 5, 428370, 106780)
X_N716_K35 = _case("X-n716-k35", "pressure", 716, 715, 35, 1007, 511940, 43373)
X_N916_K207 = _case("X-n916-k207", "pressure", 916, 915, 207, 33, 838140, 329179)

CASES = (
    X_N106_K14,
    X_N157_K13,
    X_N172_K51,
    X_N204_K19,
    X_N219_K73,
    X_N228_K23,
    X_N237_K14,
    X_N280_K17,
    X_N284_K15,
    X_N313_K71,
    X_N317_K53,
    X_N502_K39,
    X_N524_K153,
    X_N536_K96,
    X_N548_K50,
    X_N573_K30,
    X_N613_K62,
    X_N655_K131,
    X_N716_K35,
    X_N916_K207,
)
