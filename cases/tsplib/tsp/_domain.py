from __future__ import annotations

from dataclasses import dataclass
import gzip
import math
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from optagent import ExternalCallbackContext, ModelBuilder

from benchmarks.cases.base import BenchmarkCase

SOURCE = "TSPLIB95"
SOURCE_KEY = "tsplib"
PROBLEM_TYPE = "routing"
INSTANCE_TYPE = "tsp"
FAMILY = "sequence_blackbox_tsp"
BLACKBOX_TSP_MODEL_STYLE = "sequence_var_external_call"
GRAPH_TSP_MODEL_STYLE = "sequence_var_sequence_transition_sum"
MODEL_STYLE = BLACKBOX_TSP_MODEL_STYLE
DEFAULT_TSP_MODEL_STYLES = (BLACKBOX_TSP_MODEL_STYLE,)
SUPPORTED_TSP_MODEL_STYLES = (BLACKBOX_TSP_MODEL_STYLE, GRAPH_TSP_MODEL_STYLE)
RAW_DIR = Path(__file__).resolve().parent / "raw"


@dataclass(frozen=True)
class TspInstance:
    name: str
    dimension: int
    edge_weight_type: str
    coordinates: tuple[tuple[float, float], ...]
    explicit_weights: tuple[tuple[int, ...], ...] = ()

    def distance(self, left: int, right: int) -> int:
        if left == right:
            return 0
        if self.explicit_weights:
            return int(self.explicit_weights[left][right])
        left_x, left_y = self.coordinates[left]
        right_x, right_y = self.coordinates[right]
        dx = left_x - right_x
        dy = left_y - right_y
        raw = math.sqrt(dx * dx + dy * dy)
        if self.edge_weight_type == "EUC_2D":
            return int(raw + 0.5)
        if self.edge_weight_type == "CEIL_2D":
            return int(math.ceil(raw))
        raise ValueError(f"unsupported TSPLIB edge weight type: {self.edge_weight_type}")

    def tour_length(self, order: list[int] | tuple[int, ...], *, include_return_edge: bool = True) -> int:
        if len(order) != self.dimension:
            raise ValueError(f"tour length {len(order)} does not match dimension {self.dimension}")
        if set(order) != set(range(self.dimension)):
            raise ValueError("tour must be a permutation of all city ids")
        total = 0
        for index in range(1, len(order)):
            total += self.distance(int(order[index - 1]), int(order[index]))
        if include_return_edge and order:
            total += self.distance(int(order[-1]), int(order[0]))
        return int(total)


class TspCase(BenchmarkCase):
    def build_model(self, **kwargs: Any) -> ModelBuilder:
        allow_download = bool(kwargs.get("allow_download", True))
        model_style = str(kwargs.get("model_style", BLACKBOX_TSP_MODEL_STYLE))
        instance = load_tsp_case(self.to_row(), cache_dir=RAW_DIR, allow_download=allow_download)
        default_tour = list(range(instance.dimension))
        builder = ModelBuilder(metadata={"model_style": model_style})
        tour = builder.sequence_var(size=instance.dimension, default=default_tour, name="tour")

        if model_style == BLACKBOX_TSP_MODEL_STYLE:

            def tour_length(ctx: ExternalCallbackContext) -> int:
                order = [int(item) for item in ctx.value(tour)]
                return instance.tour_length(order, include_return_edge=True)

            builder.minimize(
                builder.external_call(
                    tour_length,
                    name="tour_length",
                    pure=True,
                    deterministic=True,
                    cacheable=True,
                    timeout_ms=100,
                    depends_on=(tour,),
                ),
                name="tour_length",
            )
        elif model_style == GRAPH_TSP_MODEL_STYLE:
            distance_matrix = [
                [instance.distance(left, right) for right in range(instance.dimension)]
                for left in range(instance.dimension)
            ]
            builder.minimize(
                builder.sequence_transition_sum(tour, distance_matrix, include_return_edge=True, cost_semantics="distance"),
                name="tour_length",
            )
        else:
            raise ValueError(f"unsupported TSP model style: {model_style}")

        self._set_build_context({"instance": instance, "sequence_node_id": tour.node_id, "model_style": model_style})
        return builder

    def solution_metrics(self, solution: Any, **kwargs: Any) -> dict[str, Any]:
        context = self._build_context()
        instance = context["instance"]
        sequence_node_id = int(context["sequence_node_id"])
        sequence = [int(item) for item in solution.variable_values[sequence_node_id]]
        objective = instance.tour_length(sequence, include_return_edge=True)
        return {
            "objective": float(objective),
            "decoded_solution": {
                "kind": "sequence",
                "sequence": sequence,
                "edge_weight_type": instance.edge_weight_type,
            },
            "model_style": context["model_style"],
        }


def make_tsp_case(
    *,
    benchmark_id: str,
    instance: str,
    tier: str,
    nodes: int,
    raw_path: str | Path,
    instance_url: str,
    objective: int,
    case_module: str,
    mirror_urls: tuple[str, ...] = (),
) -> TspCase:
    compare_key = f"{SOURCE_KEY}/{PROBLEM_TYPE}/{INSTANCE_TYPE}/{instance}"
    return TspCase(
        benchmark_id=benchmark_id,
        source=SOURCE,
        problem_type=PROBLEM_TYPE,
        instance_type=INSTANCE_TYPE,
        instance=instance,
        family=FAMILY,
        tier=tier,
        compare_key=compare_key,
        series_key=f"{compare_key}/{MODEL_STYLE}",
        size={"nodes": nodes},
        data={
            "raw_path": str(raw_path),
            "instance_url": instance_url,
            "mirror_urls": list(mirror_urls),
            "solution_url": "https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/STSP.html",
        },
        reference={
            "notes": "TSPLIB STSP page states all symmetric TSP instances are solved to optimality.",
            "objective": objective,
            "source_url": "https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/STSP.html",
            "status": "optimal",
            "value_kind": "optimal",
        },
        problem_description=(
            f"TSPLIB symmetric TSP instance {instance}: find the shortest Hamiltonian cycle over "
            f"{nodes} cities using the instance distance metric. The benchmark is a blackbox "
            "sequence optimization case with a published optimal tour length."
        ),
        case_module=case_module,
        modeling_notes={
            "model_style": MODEL_STYLE,
            "objective_sense": "minimize",
            "public_api_primitives": ["sequence_var", "external_call"],
        },
        extra={
            "modeling_form": "sequence_var route with external_call distance evaluator",
            "objective_sense": "minimize",
            "optagent_modeling": {
                "constraints": [
                    "sequence_var represents a permutation, so no separate all-different constraint is required"
                ],
                "data_mapping": (
                    "Read TSPLIB coordinates or explicit distances and implement the documented "
                    "TSPLIB distance metric in a callback."
                ),
                "decision_variables": [
                    f"one sequence_var tour of size {nodes}; the sequence is the city visit order"
                ],
                "external_callback": (
                    "route_cost(ctx) reads ctx.value(tour), sums consecutive arc costs, and adds "
                    "the return-to-start arc."
                ),
                "objective": "builder.minimize(builder.external_call(route_cost, name='tour_length'), name='tour_length')",
                "solver_routes": ["solve with GaConfig", "solve with AlnsConfig"],
            },
            "optagent_primitives": ["sequence_var", "external_call"],
            "recommended_evaluation": {
                "budgets_seconds": {"smoke": 10, "calibration": 60, "full": 300},
                "primary_route": (
                    "solve(..., strategy=GaConfig/AlnsConfig); exact route only for "
                    "small diagnostic comparisons"
                ),
                "strategy_candidates": ["ga", "alns"],
                "target_metrics": ["gap_to_optimum", "time_to_best", "external_call_count", "cache_hit_rate"],
            },
        },
    )


def parse_tsplib_text(text: str) -> TspInstance:
    headers: dict[str, str] = {}
    coordinates_by_id: dict[int, tuple[float, float]] = {}
    weights: list[int] = []
    section: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        upper = line.upper()
        if upper == "EOF":
            break
        if upper in {"NODE_COORD_SECTION", "EDGE_WEIGHT_SECTION"}:
            section = upper
            continue

        if section == "NODE_COORD_SECTION":
            parts = line.split()
            if len(parts) < 3:
                raise ValueError(f"invalid NODE_COORD_SECTION line: {line!r}")
            city_id = int(parts[0])
            coordinates_by_id[city_id] = (float(parts[1]), float(parts[2]))
            continue

        if section == "EDGE_WEIGHT_SECTION":
            weights.extend(int(part) for part in line.split())
            continue

        if ":" in line:
            key, value = line.split(":", 1)
        else:
            parts = line.split(maxsplit=1)
            if len(parts) != 2:
                continue
            key, value = parts
        headers[key.strip().upper()] = value.strip()

    name = headers.get("NAME")
    if not name:
        raise ValueError("TSPLIB NAME header is required")
    dimension = int(headers.get("DIMENSION", "0"))
    if dimension <= 0:
        raise ValueError("TSPLIB DIMENSION must be positive")
    edge_weight_type = headers.get("EDGE_WEIGHT_TYPE", "EUC_2D").upper()

    if coordinates_by_id:
        coordinates = tuple(coordinates_by_id[index] for index in sorted(coordinates_by_id))
        if len(coordinates) != dimension:
            raise ValueError(f"expected {dimension} coordinates, found {len(coordinates)}")
        return TspInstance(
            name=name,
            dimension=dimension,
            edge_weight_type=edge_weight_type,
            coordinates=coordinates,
        )

    if edge_weight_type == "EXPLICIT":
        matrix = _parse_explicit_matrix(weights, dimension, headers.get("EDGE_WEIGHT_FORMAT", "FULL_MATRIX").upper())
        return TspInstance(
            name=name,
            dimension=dimension,
            edge_weight_type=edge_weight_type,
            coordinates=tuple(),
            explicit_weights=matrix,
        )

    raise ValueError("TSPLIB file must contain NODE_COORD_SECTION or supported EDGE_WEIGHT_SECTION")


def load_tsp_case(
    case: dict[str, Any],
    *,
    cache_dir: str | Path = RAW_DIR,
    allow_download: bool = True,
) -> TspInstance:
    data = case.get("data", {})
    local_path = data.get("local_path")
    if local_path:
        return parse_tsplib_text(Path(local_path).read_text(encoding="utf-8"))

    instance_name = str(case.get("instance") or case["benchmark_id"].removeprefix("tsplib_"))
    path = Path(str(data.get("raw_path") or "")) if data.get("raw_path") else Path(cache_dir) / f"{instance_name}.tsp"
    if path.exists():
        return parse_tsplib_text(path.read_text(encoding="utf-8"))

    urls = [str(url) for url in [data.get("instance_url"), *data.get("mirror_urls", [])] if url]
    if not urls:
        raise ValueError(f"case {case['benchmark_id']} does not provide an instance_url")
    if not allow_download:
        raise FileNotFoundError(f"cached TSPLIB file not found and downloads are disabled: {path}")

    path.parent.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    for url in urls:
        try:
            raw = _download_bytes(url, timeout=60)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            errors.append(f"{url}: {type(exc).__name__}: {exc}")
            continue
        if url.endswith(".gz"):
            raw = gzip.decompress(raw)
        text = raw.decode("utf-8", errors="replace")
        path.write_text(text, encoding="utf-8")
        return parse_tsplib_text(text)
    raise RuntimeError(
        f"failed to download TSPLIB case {case['benchmark_id']} from {len(urls)} source(s): "
        + " | ".join(errors)
    )


def _parse_explicit_matrix(
    weights: list[int],
    dimension: int,
    edge_weight_format: str,
) -> tuple[tuple[int, ...], ...]:
    if edge_weight_format == "FULL_MATRIX":
        expected = dimension * dimension
        if len(weights) != expected:
            raise ValueError(f"expected {expected} FULL_MATRIX weights, found {len(weights)}")
        return tuple(
            tuple(weights[row * dimension + col] for col in range(dimension))
            for row in range(dimension)
        )
    raise ValueError(f"unsupported TSPLIB EDGE_WEIGHT_FORMAT: {edge_weight_format}")


def _download_bytes(url: str, *, timeout: int) -> bytes:
    request = Request(url, headers={"User-Agent": "optagent-benchmark/1.0"})
    with urlopen(request, timeout=timeout) as response:
        return response.read()
