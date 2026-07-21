from __future__ import annotations

from dataclasses import dataclass, replace
import json
import math
from pathlib import Path
from typing import Any

from optagent import ModelBuilder

from benchmarks.cases.base import BenchmarkCase, SolutionVerification

SOURCE = "CVRP2LIB"
SOURCE_KEY = "cvrp2lib"
PROBLEM_TYPE = "CVRP_XML"
INSTANCE_TYPE = "cvrp_xml"
FAMILY = "capacitated_vehicle_routing_variable_fleet"
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
    distance_matrix: tuple[tuple[float, ...], ...] | None = None

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

    def distance(self, left: int, right: int) -> float:
        if left == right:
            return 0.0
        edge_weight_type = self.edge_weight_type.upper()
        if edge_weight_type == "EXPLICIT":
            if self.distance_matrix is None:
                raise ValueError(f"EXPLICIT CVRP2LIB instance {self.name!r} has no distance matrix")
            return self.distance_matrix[left][right]
        first = self.nodes[left]
        second = self.nodes[right]
        if first.x is None or first.y is None or second.x is None or second.y is None:
            raise ValueError(f"CVRP2LIB instance {self.name!r} lacks coordinates for {edge_weight_type}")
        dx = abs(first.x - second.x)
        dy = abs(first.y - second.y)
        if edge_weight_type in {"EUC_2D", "EUC_3D"}:
            return math.hypot(dx, dy)
        if edge_weight_type == "CEIL_2D":
            return float(math.ceil(math.hypot(dx, dy)))
        if edge_weight_type == "MAN_2D":
            return dx + dy
        if edge_weight_type == "MAX_2D":
            return max(dx, dy)
        raise ValueError(f"Unsupported CVRP2LIB edge_weight_type: {self.edge_weight_type}")

class CvrpXmlCase(BenchmarkCase):
    def build_model(self, **kwargs: Any) -> ModelBuilder:
        raise NotImplementedError(
            "CVRP_XML variable-fleet model construction is intentionally pending"
        )

    def solution_metrics(self, solution: Any, **kwargs: Any) -> dict[str, Any]:
        raise NotImplementedError("CVRP_XML solution decoding is intentionally pending")

    def verify_solution(self, solution: Any, **kwargs: Any) -> SolutionVerification:
        context = self._build_context()
        instance: CvrpInstance = context["instance"]
        values = getattr(solution, "variable_values", {}) or {}
        arc_variables = context.get("arc_variables", {})
        selected_arcs: set[tuple[int, int]] = set()
        violations: list[str] = []
        for arc, variable in arc_variables.items():
            raw_value = values.get(variable.node_id, 0)
            try:
                value = float(raw_value)
            except (TypeError, ValueError):
                violations.append(f"arc {arc} must have a numeric value")
                continue
            if not math.isclose(value, 0.0, abs_tol=1e-6) and not math.isclose(value, 1.0, abs_tol=1e-6):
                violations.append(f"arc {arc} must be binary")
            elif value > 0.5:
                selected_arcs.add(arc)

        depot = context["depot"]
        customers = set(context["customers"])
        incoming = {node: 0 for node in customers}
        outgoing = {node: 0 for node in customers}
        depot_incoming = 0
        depot_outgoing = 0
        for left, right in selected_arcs:
            if right in incoming:
                incoming[right] += 1
            if left in outgoing:
                outgoing[left] += 1
            if right == depot:
                depot_incoming += 1
            if left == depot:
                depot_outgoing += 1
        for customer in sorted(customers):
            if incoming[customer] != 1:
                violations.append(f"customer {customer} incoming degree is {incoming[customer]}, expected 1")
            if outgoing[customer] != 1:
                violations.append(f"customer {customer} outgoing degree is {outgoing[customer]}, expected 1")
        expected_routes = instance.vehicles or instance.reference.get("route_count")
        if expected_routes is not None:
            if depot_incoming != expected_routes:
                violations.append(f"depot incoming degree is {depot_incoming}, expected {expected_routes}")
            if depot_outgoing != expected_routes:
                violations.append(f"depot outgoing degree is {depot_outgoing}, expected {expected_routes}")

        routes = _decode_routes(selected_arcs, depot=depot, customer_count=instance.customer_count)
        visited = [customer for route in routes for customer in route]
        if expected_routes is not None and len(routes) != expected_routes:
            violations.append(f"decoded route count is {len(routes)}, expected {expected_routes}")
        if len(visited) != len(customers) or set(visited) != customers:
            violations.append("decoded routes do not visit every customer exactly once")
        if len(visited) != len(set(visited)):
            violations.append("decoded routes visit a customer more than once")
        demands = {index: instance.nodes[index].demand for index in customers}
        for route_number, route in enumerate(routes, start=1):
            load = sum(demands[index] for index in route)
            if load > instance.capacity + 1e-9:
                violations.append(f"route {route_number} load {load:g} exceeds capacity {instance.capacity:g}")
        if violations:
            return SolutionVerification.failed(*violations)
        objective = sum(instance.distance(left, right) for left, right in selected_arcs)
        return SolutionVerification.accepted(objective=float(objective))


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



def parse_cvrp_vrp_text(text: str, *, expected_name: str | None = None) -> tuple[tuple[float, ...], ...]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    headers: dict[str, str] = {}
    section_index: int | None = None
    for index, line in enumerate(lines):
        upper = line.upper()
        if upper == "EDGE_WEIGHT_SECTION":
            section_index = index
            break
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip().upper()] = value.strip()
    if section_index is None:
        raise ValueError("CVRP2LIB .vrp is missing EDGE_WEIGHT_SECTION")
    name = headers.get("NAME", "")
    if expected_name is not None and name != expected_name:
        raise ValueError(f"CVRP2LIB .vrp name {name!r} does not match expected {expected_name!r}")
    if headers.get("EDGE_WEIGHT_TYPE", "").upper() != "EXPLICIT":
        raise ValueError("CVRP2LIB .vrp parser expects EDGE_WEIGHT_TYPE EXPLICIT")
    if headers.get("EDGE_WEIGHT_FORMAT", "").upper() != "LOWER_ROW":
        raise ValueError(
            f"unsupported EXPLICIT CVRP2LIB .vrp format: {headers.get('EDGE_WEIGHT_FORMAT', '')!r}"
        )
    try:
        dimension = int(headers["DIMENSION"])
    except (KeyError, ValueError) as exc:
        raise ValueError("CVRP2LIB .vrp requires an integer DIMENSION") from exc
    values: list[float] = []
    for line in lines[section_index + 1 :]:
        upper = line.upper()
        if upper == "EOF" or upper.endswith("_SECTION"):
            break
        values.extend(float(item) for item in line.split())
    expected_values = dimension * (dimension - 1) // 2
    if len(values) != expected_values:
        raise ValueError(
            f"CVRP2LIB LOWER_ROW distance count mismatch: expected {expected_values}, found {len(values)}"
        )
    matrix = [[0.0 for _ in range(dimension)] for _ in range(dimension)]
    cursor = 0
    for row in range(1, dimension):
        for column in range(row):
            value = values[cursor]
            cursor += 1
            matrix[row][column] = value
            matrix[column][row] = value
    return tuple(tuple(row) for row in matrix)


def _attach_explicit_distance_matrix(
    instance: CvrpInstance,
    *,
    json_path: Path,
    data: dict[str, Any],
) -> CvrpInstance:
    if instance.edge_weight_type.upper() != "EXPLICIT":
        return instance
    raw_vrp_path = data.get("source_vrp_path")
    vrp_path = Path(str(raw_vrp_path)) if raw_vrp_path else json_path.with_suffix(".vrp")
    if not vrp_path.is_absolute():
        vrp_path = json_path.parent / vrp_path
    if not vrp_path.exists():
        raise FileNotFoundError(f"EXPLICIT CVRP2LIB .vrp file not found: {vrp_path}")
    matrix = parse_cvrp_vrp_text(
        vrp_path.read_text(encoding="utf-8"),
        expected_name=instance.name,
    )
    if len(matrix) != instance.node_count:
        raise ValueError(
            f"EXPLICIT CVRP2LIB matrix dimension {len(matrix)} does not match node count {instance.node_count}"
        )
    return replace(instance, distance_matrix=matrix)


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
        json_path = Path(local_path)
        instance = load_cvrp_json(json_path, expected_name=source_instance)
        return _attach_explicit_distance_matrix(instance, json_path=json_path, data=data)

    path = (
        Path(str(data["raw_path"]))
        if data.get("raw_path")
        else Path(cache_dir) / f"{source_instance}.json"
    )
    if path.exists():
        instance = load_cvrp_json(path, expected_name=source_instance)
        return _attach_explicit_distance_matrix(instance, json_path=path, data=data)
    if not allow_download:
        raise FileNotFoundError(f"cached CVRP2LIB file not found and downloads are disabled: {path}")
    raise FileNotFoundError(f"cached CVRP2LIB file not found: {path}")



def _decode_routes(
    selected_arcs: set[tuple[int, int]],
    *,
    depot: int,
    customer_count: int,
) -> list[list[int]]:
    successors: dict[int, int] = {}
    for left, right in selected_arcs:
        successors[left] = right
    routes: list[list[int]] = []
    starts = sorted(right for left, right in selected_arcs if left == depot and right != depot)
    for start in starts:
        route: list[int] = []
        current = start
        visited: set[int] = set()
        while current != depot and current not in visited and len(route) <= customer_count:
            visited.add(current)
            route.append(current)
            next_node = successors.get(current)
            if next_node is None:
                break
            current = next_node
        routes.append(route)
    return routes
