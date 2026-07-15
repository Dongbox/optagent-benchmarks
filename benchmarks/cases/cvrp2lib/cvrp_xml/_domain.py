from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from optagent import ModelBuilder

from benchmarks.cases.base import BenchmarkCase

SOURCE = "CVRP2LIB"
SOURCE_KEY = "cvrp2lib"
PROBLEM_TYPE = "CVRP_XML"
INSTANCE_TYPE = "cvrp_xml"
FAMILY = "capacitated_vehicle_routing"
MODEL_STYLE = "binary_arc_variable_fleet_single_commodity_flow"
RAW_DIR = Path(__file__).resolve().parent / "raw"
DOCUMENTATION_URL = "https://galgos.inf.puc-rio.br/cvrplib/en/xml100"


@dataclass(frozen=True)
class CvrpNode:
    node_id: int
    x: float | None
    y: float | None
    demand: float
    is_depot: bool


@dataclass(frozen=True)
class CvrpInstance:
    name: str
    series: str
    edge_weight_type: str
    capacity: float
    vehicles: int | None
    depot_id: int
    nodes: tuple[CvrpNode, ...]
    statistics: dict[str, Any]
    reference: dict[str, Any]

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def customer_count(self) -> int:
        return sum(not node.is_depot for node in self.nodes)

    @property
    def directed_arc_count(self) -> int:
        return self.node_count * max(0, self.node_count - 1)

    @property
    def customer_nodes(self) -> tuple[CvrpNode, ...]:
        return tuple(node for node in self.nodes if not node.is_depot)


class CvrpXmlCase(BenchmarkCase):
    def build_model(self, **kwargs: Any) -> ModelBuilder:
        raise NotImplementedError(
            "CVRP_XML variable-fleet model construction is intentionally pending"
        )

    def solution_metrics(self, solution: Any, **kwargs: Any) -> dict[str, Any]:
        raise NotImplementedError("CVRP_XML solution decoding is intentionally pending")


def make_cvrp_case(
    *,
    benchmark_id: str,
    instance: str,
    source_instance: str,
    tier: str,
    nodes: int,
    customers: int,
    vehicles: int | None,
    capacity: int | float,
    directed_arcs: int,
    raw_path: str | Path,
    objective: int | float,
    reference_route_count: int,
    case_module: str,
    reference_status: str = "optimal",
    reference_value_kind: str = "optimal",
) -> CvrpXmlCase:
    compare_key = f"{SOURCE_KEY}/{PROBLEM_TYPE}/{INSTANCE_TYPE}/{instance}"
    raw_path = Path(raw_path)
    reference = {
        "cost": objective,
        "objective": objective,
        "route_count": reference_route_count,
        "vehicles": reference_route_count,
        "source_url": DOCUMENTATION_URL,
        "status": reference_status,
        "value_kind": reference_value_kind,
    }
    data = {
        "documentation_url": DOCUMENTATION_URL,
        "raw_path": str(raw_path),
        "source_instance": source_instance,
        "source_vrp_path": str(raw_path.with_suffix(".vrp")),
        "solution_path": str(raw_path.with_suffix(".sol")),
    }

    return CvrpXmlCase(
        benchmark_id=benchmark_id,
        source=SOURCE,
        problem_type=PROBLEM_TYPE,
        instance_type=INSTANCE_TYPE,
        instance=instance,
        family=FAMILY,
        tier=tier,
        compare_key=compare_key,
        series_key=f"{compare_key}/{MODEL_STYLE}",
        size={
            "nodes": nodes,
            "customers": customers,
            "vehicles": vehicles,
            "capacity": capacity,
            "directed_arcs": directed_arcs,
        },
        data=data,
        reference=reference,
        problem_description=(
            f"CVRP2LIB CVRP_XML instance {source_instance}: serve {customers} customers "
            f"with capacity-{capacity} vehicles while minimizing total route distance; "
            "the input vehicle count is not fixed."
        ),
        case_module=case_module,
        modeling_notes={
            "implementation_status": "scaffold",
            "model_style": MODEL_STYLE,
            "objective_sense": "minimize",
            "vehicle_count_semantics": "variable_input_vehicle_count",
            "public_api_primitives": ["bool_var", "int_var", "constraint", "minimize"],
        },
    )


def parse_cvrp_json(text: str, *, expected_name: str | None = None) -> CvrpInstance:
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("CVRP2LIB JSON root must be an object")

    name = str(payload.get("name") or "").strip()
    if not name:
        raise ValueError("CVRP2LIB JSON requires a name")
    if expected_name is not None and name != expected_name:
        raise ValueError(f"CVRP2LIB JSON name {name!r} does not match expected {expected_name!r}")

    size = payload.get("size")
    depot = payload.get("depot")
    raw_nodes = payload.get("nodes")
    if not isinstance(size, dict):
        raise ValueError("CVRP2LIB JSON requires a size object")
    if not isinstance(depot, dict) or depot.get("id") is None:
        raise ValueError("CVRP2LIB JSON requires a depot id")
    if not isinstance(raw_nodes, list) or not raw_nodes:
        raise ValueError("CVRP2LIB JSON requires a non-empty nodes list")

    declared_nodes = int(size.get("nodes") or 0)
    declared_customers = int(size.get("customers") or 0)
    raw_vehicles = size.get("vehicles")
    vehicles = int(raw_vehicles) if raw_vehicles is not None else None
    capacity = float(size.get("capacity") or 0)
    depot_id = int(depot["id"])
    if declared_nodes <= 1 or declared_customers <= 0:
        raise ValueError("CVRP2LIB JSON requires positive node and customer counts")
    if vehicles is not None and vehicles <= 0:
        raise ValueError("CVRP2LIB JSON vehicles must be positive when provided")
    if capacity <= 0:
        raise ValueError("CVRP2LIB JSON requires positive capacity")

    nodes: list[CvrpNode] = []
    seen_ids: set[int] = set()
    for raw_node in raw_nodes:
        if not isinstance(raw_node, dict):
            raise ValueError("CVRP2LIB node rows must be objects")
        raw_x = raw_node.get("x")
        raw_y = raw_node.get("y")
        node = CvrpNode(
            node_id=int(raw_node["id"]),
            x=float(raw_x) if raw_x is not None else None,
            y=float(raw_y) if raw_y is not None else None,
            demand=float(raw_node["demand"]),
            is_depot=bool(raw_node.get("is_depot", False)),
        )
        if node.node_id in seen_ids:
            raise ValueError(f"duplicate CVRP2LIB node id: {node.node_id}")
        if node.demand < 0:
            raise ValueError(f"CVRP2LIB node demand must be non-negative: {node.node_id}")
        seen_ids.add(node.node_id)
        nodes.append(node)

    depot_nodes = [node for node in nodes if node.is_depot]
    if len(nodes) != declared_nodes:
        raise ValueError(f"expected {declared_nodes} nodes, found {len(nodes)}")
    if len(depot_nodes) != 1 or depot_nodes[0].node_id != depot_id:
        raise ValueError("CVRP2LIB JSON must identify exactly one matching depot node")
    if sum(not node.is_depot for node in nodes) != declared_customers:
        raise ValueError(f"expected {declared_customers} customers")

    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    statistics = payload.get("statistics") if isinstance(payload.get("statistics"), dict) else {}
    reference = payload.get("reference") if isinstance(payload.get("reference"), dict) else {}
    return CvrpInstance(
        name=name,
        series=str(payload.get("series") or ""),
        edge_weight_type=str(metadata.get("edge_weight_type") or ""),
        capacity=capacity,
        vehicles=vehicles,
        depot_id=depot_id,
        nodes=tuple(sorted(nodes, key=lambda item: item.node_id)),
        statistics=dict(statistics),
        reference=dict(reference),
    )


def load_cvrp_json(path: str | Path, *, expected_name: str | None = None) -> CvrpInstance:
    path = Path(path)
    return parse_cvrp_json(path.read_text(encoding="utf-8"), expected_name=expected_name)


def load_cvrp_case(
    case: dict[str, Any],
    *,
    cache_dir: str | Path = RAW_DIR,
    allow_download: bool = True,
) -> CvrpInstance:
    data = case.get("data", {})
    source_instance = str(data.get("source_instance") or case.get("instance") or "")
    local_path = data.get("local_path")
    if local_path:
        return load_cvrp_json(local_path, expected_name=source_instance)

    path = (
        Path(str(data["raw_path"]))
        if data.get("raw_path")
        else Path(cache_dir) / f"{source_instance}.json"
    )
    if path.exists():
        return load_cvrp_json(path, expected_name=source_instance)
    if not allow_download:
        raise FileNotFoundError(f"cached CVRP2LIB file not found and downloads are disabled: {path}")
    raise FileNotFoundError(f"cached CVRP2LIB file not found: {path}")
