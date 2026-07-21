from __future__ import annotations

from dataclasses import dataclass, replace
import json
import math
from pathlib import Path
from typing import Any

from optagent import ModelBuilder

from benchmarks.cases.base import BenchmarkCase, SolutionVerification

SOURCE = "CVRPLIB"
SOURCE_KEY = "cvrplib"
PROBLEM_TYPE = "routing"
INSTANCE_TYPE = "cvrp"
FAMILY = "capacitated_vehicle_routing_fixed_fleet"
MODEL_STYLE = "binary_arc_node_load_mtz"
RAW_DIR = Path(__file__).resolve().parent / "raw"
DOCUMENTATION_URL = "http://vrp.atd-lab.inf.puc-rio.br/index.php/en/"


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
    vehicles: int
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
        """Return the instance distance between two internal node indices."""
        if left == right:
            return 0.0
        edge_weight_type = self.edge_weight_type.upper()
        if edge_weight_type == "EXPLICIT":
            if self.distance_matrix is None:
                raise ValueError(f"EXPLICIT CVRPLIB instance {self.name!r} has no distance matrix")
            return self.distance_matrix[left][right]
        first = self.nodes[left]
        second = self.nodes[right]
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
        raise ValueError(
            f"Unsupported CVRPLIB edge_weight_type: {self.edge_weight_type}"
        )


class CvrpCase(BenchmarkCase):
    def build_model(self, **kwargs: Any) -> ModelBuilder:
        allow_download = bool(kwargs.get("allow_download", True))
        instance = load_cvrp_case(
            self.to_row(),
            cache_dir=RAW_DIR,
            allow_download=allow_download,
        )

        node_count = instance.node_count
        depot = next(
            index for index, node in enumerate(instance.nodes) if node.is_depot
        )
        customers = tuple(index for index in range(node_count) if index != depot)
        arcs = tuple(
            (left, right)
            for left in range(node_count)
            for right in range(node_count)
            if left != right
        )
        demands = {
            index: int(round(instance.nodes[index].demand)) for index in customers
        }
        reference_x, _reference_flow = _reference_defaults(instance, depot, customers)
        # Keep reference-route parsing/validation available, but start the model
        # with neutral zero defaults rather than seeding it from the reference.
        reference_x = {arc: 0 for arc in reference_x}

        builder = ModelBuilder(
            metadata={
                "model_style": MODEL_STYLE,
                "objective_sense": "minimize",
                "problem_type": "CVRP",
            }
        )
        arc_variables = {
            arc: builder.bool_var(
                default=bool(reference_x.get(arc, False)),
                name=f"x_{arc[0]}_{arc[1]}",
            )
            for arc in arcs
        }
        load_variables = {
            customer: builder.int_var(
                default=0,
                lb=0,
                ub=int(round(instance.capacity)),
                name=f"u_{customer}",
            )
            for customer in customers
        }

        for customer in customers:
            incoming = _sum_expr(
                builder,
                (arc_variables[(left, customer)]
                for left in range(node_count)
                if left != customer
                )
            )
            outgoing = _sum_expr(
                builder,
                (arc_variables[(customer, right)]
                for right in range(node_count)
                if right != customer
                )
            )
            builder.constraint(incoming == 1, name=f"visit_in_{customer}")
            builder.constraint(outgoing == 1, name=f"visit_out_{customer}")

        depot_incoming = _sum_expr(
            builder,
            (arc_variables[(left, depot)] for left in customers)
        )
        depot_outgoing = _sum_expr(
            builder,
            (arc_variables[(depot, right)] for right in customers)
        )
        builder.constraint(
            depot_incoming == instance.vehicles,
            name="depot_incoming_vehicles",
        )
        builder.constraint(
            depot_outgoing == instance.vehicles,
            name="depot_outgoing_vehicles",
        )

        capacity = int(round(instance.capacity))
        for customer in customers:
            builder.constraint(
                load_variables[customer] >= demands[customer],
                name=f"load_lower_{customer}",
            )
        for left in customers:
            for right in customers:
                if left == right:
                    continue
                builder.constraint(
                    load_variables[left]
                    - load_variables[right]
                    + capacity * arc_variables[(left, right)]
                    <= capacity - demands[right],
                    name=f"load_transition_{left}_{right}",
                )

        objective = _weighted_sum(
            builder,
            (
                instance.distance(left, right) * arc_variables[(left, right)]
                for left, right in arcs
            ),
        )
        builder.minimize(objective, name="total_distance")
        self._set_build_context(
            {
                "instance": instance,
                "depot": depot,
                "customers": customers,
                "arc_variables": arc_variables,
                "load_variables": load_variables,
            }
        )
        return builder

    def solution_metrics(self, solution: Any, **kwargs: Any) -> dict[str, Any]:
        context = self._build_context()
        instance: CvrpInstance = context["instance"]
        values = getattr(solution, "variable_values", {}) or {}
        arc_variables = context["arc_variables"]
        selected_arcs = {
            arc
            for arc, variable in arc_variables.items()
            if float(values.get(variable.node_id, 0.0)) > 0.5
        }
        routes = _decode_routes(
            selected_arcs,
            depot=context["depot"],
            customer_count=instance.customer_count,
        )
        customer_output_ids = {
            index: position + 1
            for position, index in enumerate(context["customers"])
        }
        routes = [
            [customer_output_ids[index] for index in route]
            for route in routes
        ]
        objective = sum(
            instance.distance(left, right) for left, right in selected_arcs
        )
        feasible = bool(getattr(solution, "feasible", False))
        return {
            "objective": float(objective) if feasible else None,
            "route_count": len(routes) if feasible else None,
            "vehicle_count": len(routes) if feasible else None,
            "routes": routes if feasible else [],
            "selected_arc_count": len(selected_arcs),
            "raw_objective": getattr(solution, "objective_value", None),
            "model_style": MODEL_STYLE,
            "flow_formulation": "node_load_mtz",
            "capacity": instance.capacity,
            "vehicles": instance.vehicles,
        }

    def verify_solution(self, solution: Any, **kwargs: Any) -> SolutionVerification:
        context = self._build_context()
        instance: CvrpInstance = context["instance"]
        values = getattr(solution, "variable_values", {}) or {}
        arc_variables = context["arc_variables"]
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
        if depot_incoming != instance.vehicles:
            violations.append(f"depot incoming degree is {depot_incoming}, expected {instance.vehicles}")
        if depot_outgoing != instance.vehicles:
            violations.append(f"depot outgoing degree is {depot_outgoing}, expected {instance.vehicles}")

        routes = _decode_routes(
            selected_arcs,
            depot=depot,
            customer_count=instance.customer_count,
        )
        visited = [customer for route in routes for customer in route]
        if len(routes) != instance.vehicles:
            violations.append(f"decoded route count is {len(routes)}, expected {instance.vehicles}")
        if len(visited) != len(customers) or set(visited) != customers:
            violations.append("decoded routes do not visit every customer exactly once")
        if len(visited) != len(set(visited)):
            violations.append("decoded routes visit a customer more than once")
        demands = {index: instance.nodes[index].demand for index in customers}
        for route_number, route in enumerate(routes, start=1):
            load = sum(demands[index] for index in route)
            if load > instance.capacity + 1e-9:
                violations.append(
                    f"route {route_number} load {load:g} exceeds capacity {instance.capacity:g}"
                )

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
    vehicles: int,
    capacity: int | float,
    directed_arcs: int,
    raw_path: str | Path,
    objective: int | float,
    case_module: str,
    reference_route_count: int | None = None,
    reference_status: str = "best_known",
    reference_value_kind: str = "best_known",
) -> CvrpCase:
    compare_key = f"{SOURCE_KEY}/{PROBLEM_TYPE}/{INSTANCE_TYPE}/{instance}"
    raw_path = Path(raw_path)
    route_count = vehicles if reference_route_count is None else reference_route_count
    reference = {
        "cost": objective,
        "objective": objective,
        "route_count": route_count,
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

    return CvrpCase(
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
            f"CVRPLIB CVRP instance {source_instance}: serve {customers} customers with exactly "
            f"{vehicles} capacity-{capacity} vehicles while minimizing total route distance."
        ),
        case_module=case_module,
        modeling_notes={
            "implementation_status": "implemented",
            "model_style": MODEL_STYLE,
            "objective_sense": "minimize",
            "public_api_primitives": ["bool_var", "int_var", "constraint", "minimize"],
        },
    )


def parse_cvrplib_json(text: str, *, expected_name: str | None = None) -> CvrpInstance:
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("CVRPLIB JSON root must be an object")

    name = str(payload.get("name") or "").strip()
    if not name:
        raise ValueError("CVRPLIB JSON requires a name")
    if expected_name is not None and name != expected_name:
        raise ValueError(f"CVRPLIB JSON name {name!r} does not match expected {expected_name!r}")

    size = payload.get("size")
    depot = payload.get("depot")
    raw_nodes = payload.get("nodes")
    if not isinstance(size, dict):
        raise ValueError("CVRPLIB JSON requires a size object")
    if not isinstance(depot, dict) or depot.get("id") is None:
        raise ValueError("CVRPLIB JSON requires a depot id")
    if not isinstance(raw_nodes, list) or not raw_nodes:
        raise ValueError("CVRPLIB JSON requires a non-empty nodes list")

    declared_nodes = int(size.get("nodes") or 0)
    declared_customers = int(size.get("customers") or 0)
    vehicles = int(size.get("vehicles") or 0)
    capacity = float(size.get("capacity") or 0)
    depot_id = int(depot["id"])
    if declared_nodes <= 1 or declared_customers <= 0:
        raise ValueError("CVRPLIB JSON requires positive node and customer counts")
    if vehicles <= 0 or capacity <= 0:
        raise ValueError("CVRPLIB JSON requires positive vehicles and capacity")

    nodes: list[CvrpNode] = []
    seen_ids: set[int] = set()
    for raw_node in raw_nodes:
        if not isinstance(raw_node, dict):
            raise ValueError("CVRPLIB node rows must be objects")
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
            raise ValueError(f"duplicate CVRPLIB node id: {node.node_id}")
        if node.demand < 0:
            raise ValueError(f"CVRPLIB node demand must be non-negative: {node.node_id}")
        seen_ids.add(node.node_id)
        nodes.append(node)

    depot_nodes = [node for node in nodes if node.is_depot]
    if len(nodes) != declared_nodes:
        raise ValueError(f"expected {declared_nodes} nodes, found {len(nodes)}")
    if len(depot_nodes) != 1 or depot_nodes[0].node_id != depot_id:
        raise ValueError("CVRPLIB JSON must identify exactly one matching depot node")
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



def parse_cvrplib_vrp_text(text: str, *, expected_name: str | None = None) -> tuple[tuple[float, ...], ...]:
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
        raise ValueError("CVRPLIB .vrp is missing EDGE_WEIGHT_SECTION")
    name = headers.get("NAME", "")
    if expected_name is not None and name != expected_name:
        raise ValueError(f"CVRPLIB .vrp name {name!r} does not match expected {expected_name!r}")
    edge_type = headers.get("EDGE_WEIGHT_TYPE", "").upper()
    edge_format = headers.get("EDGE_WEIGHT_FORMAT", "").upper()
    if edge_type != "EXPLICIT":
        raise ValueError(f"CVRPLIB .vrp distance type {edge_type!r} is not EXPLICIT")
    if edge_format != "LOWER_ROW":
        raise ValueError(f"unsupported EXPLICIT CVRPLIB .vrp format: {edge_format!r}")
    try:
        dimension = int(headers["DIMENSION"])
    except (KeyError, ValueError) as exc:
        raise ValueError("CVRPLIB .vrp requires an integer DIMENSION") from exc
    values: list[float] = []
    for line in lines[section_index + 1 :]:
        upper = line.upper()
        if upper == "EOF" or upper.endswith("_SECTION"):
            break
        values.extend(float(item) for item in line.split())
    expected_values = dimension * (dimension - 1) // 2
    if len(values) != expected_values:
        raise ValueError(
            f"CVRPLIB LOWER_ROW distance count mismatch: expected {expected_values}, found {len(values)}"
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
        raise FileNotFoundError(f"EXPLICIT CVRPLIB .vrp file not found: {vrp_path}")
    matrix = parse_cvrplib_vrp_text(
        vrp_path.read_text(encoding="utf-8"),
        expected_name=instance.name,
    )
    if len(matrix) != instance.node_count:
        raise ValueError(
            f"EXPLICIT CVRPLIB matrix dimension {len(matrix)} does not match node count {instance.node_count}"
        )
    return replace(instance, distance_matrix=matrix)


def load_cvrp_json(path: str | Path, *, expected_name: str | None = None) -> CvrpInstance:
    path = Path(path)
    return parse_cvrplib_json(path.read_text(encoding="utf-8"), expected_name=expected_name)


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
        raise FileNotFoundError(f"cached CVRPLIB file not found and downloads are disabled: {path}")
    raise FileNotFoundError(f"cached CVRPLIB file not found: {path}")


def _sum_expr(builder: ModelBuilder, expressions: Any) -> Any:
    values = list(expressions)
    if not values:
        return builder.const(0)
    return builder.sum(*values)


def _weighted_sum(builder: ModelBuilder, terms: Any) -> Any:
    return _sum_expr(builder, terms)


def _reference_defaults(
    instance: CvrpInstance,
    depot: int,
    customers: tuple[int, ...],
) -> tuple[dict[tuple[int, int], int], dict[tuple[int, int], int]]:
    routes = instance.reference.get("routes")
    if not isinstance(routes, list) or len(routes) != instance.vehicles:
        return {}, {}

    customer_by_solution_id = {
        position + 1: index for position, index in enumerate(customers)
    }
    demands = {
        index: int(round(instance.nodes[index].demand)) for index in customers
    }
    arc_defaults: dict[tuple[int, int], int] = {}
    flow_defaults: dict[tuple[int, int], int] = {}
    seen: set[int] = set()

    try:
        for raw_route in routes:
            if not isinstance(raw_route, list) or not raw_route:
                return {}, {}
            route = [customer_by_solution_id[int(item)] for item in raw_route]
            if len(set(route)) != len(route) or seen.intersection(route):
                return {}, {}
            seen.update(route)
            load = sum(demands[index] for index in route)
            if load > int(round(instance.capacity)):
                return {}, {}

            path = [depot, *route, depot]
            remaining = [
                sum(demands[index] for index in route[position:])
                for position in range(len(route))
            ]
            for position, (left, right) in enumerate(zip(path, path[1:])):
                arc_defaults[(left, right)] = 1
                flow_defaults[(left, right)] = (
                    remaining[position] if right != depot else 0
                )
    except (KeyError, TypeError, ValueError):
        return {}, {}

    if seen != set(customers):
        return {}, {}
    return arc_defaults, flow_defaults


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
    for start in sorted(
        right for left, right in selected_arcs if left == depot and right != depot
    ):
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
