from __future__ import annotations

from benchmarks.cases.cvrplib.cvrp._domain import RAW_DIR, make_cvrp_case

CASE_MODULE = __name__


def _case(name: str, vehicles: int, capacity: int, objective: int):
    instance = name.lower()
    return make_cvrp_case(
        benchmark_id=f"cvrplib_{instance}",
        instance=instance,
        source_instance=name,
        tier="calibration",
        nodes=101,
        customers=100,
        vehicles=vehicles,
        capacity=capacity,
        directed_arcs=10100,
        raw_path=RAW_DIR / f"{name}.json",
        objective=objective,
        case_module=CASE_MODULE,
        reference_status="optimal",
        reference_value_kind="optimal",
    )


XML100_1111_04 = _case("XML100_1111_04", 34, 3, 37554)
XML100_1211_01 = _case("XML100_1211_01", 34, 3, 44590)
XML100_1211_02 = _case("XML100_1211_02", 34, 3, 59187)
XML100_1211_10 = _case("XML100_1211_10", 34, 3, 41618)
XML100_1211_15 = _case("XML100_1211_15", 25, 4, 16187)
XML100_1212_09 = _case("XML100_1212_09", 20, 5, 20586)
XML100_1213_06 = _case("XML100_1213_06", 10, 10, 12899)
XML100_1215_22 = _case("XML100_1215_22", 6, 19, 11972)
XML100_1216_04 = _case("XML100_1216_04", 3, 38, 6068)
XML100_1221_07 = _case("XML100_1221_07", 21, 27, 19773)
XML100_1232_22 = _case("XML100_1232_22", 17, 46, 18369)
XML100_1241_06 = _case("XML100_1241_06", 32, 177, 27762)
XML100_1246_16 = _case("XML100_1246_16", 3, 2371, 5439)
XML100_1246_25 = _case("XML100_1246_25", 4, 1664, 5301)
XML100_1253_05 = _case("XML100_1253_05", 12, 631, 10310)
XML100_1253_06 = _case("XML100_1253_06", 9, 873, 16878)
XML100_1261_02 = _case("XML100_1261_02", 33, 183, 24376)
XML100_1272_26 = _case("XML100_1272_26", 15, 134, 19200)
XML100_1273_14 = _case("XML100_1273_14", 9, 142, 17552)
XML100_1274_15 = _case("XML100_1274_15", 7, 179, 5827)
XML100_2261_21 = _case("XML100_2261_21", 21, 226, 22453)
XML100_2376_10 = _case("XML100_2376_10", 2, 371, 7533)
XML100_3224_11 = _case("XML100_3224_11", 7, 73, 10464)
XML100_3236_21 = _case("XML100_3236_21", 3, 349, 6407)
XML100_3275_11 = _case("XML100_3275_11", 5, 201, 8078)

CASES = (
    XML100_1111_04,
    XML100_1211_01,
    XML100_1211_02,
    XML100_1211_10,
    XML100_1211_15,
    XML100_1212_09,
    XML100_1213_06,
    XML100_1215_22,
    XML100_1216_04,
    XML100_1221_07,
    XML100_1232_22,
    XML100_1241_06,
    XML100_1246_16,
    XML100_1246_25,
    XML100_1253_05,
    XML100_1253_06,
    XML100_1261_02,
    XML100_1272_26,
    XML100_1273_14,
    XML100_1274_15,
    XML100_2261_21,
    XML100_2376_10,
    XML100_3224_11,
    XML100_3236_21,
    XML100_3275_11,
)
