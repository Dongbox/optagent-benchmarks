from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import gzip
import json
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent / "data"
COIL_DATA_PATH = DATA_DIR / "steel_coils.json"
SAMPLE303_DATA_PATH = DATA_DIR / "sample_303.json"
GRAPH900_DATA_PATH = DATA_DIR / "graphs_dense_900.jsonl.gz"
GRAPH1000_DATA_PATH = DATA_DIR / "graphs_sparse_1000.jsonl.gz"


@dataclass(frozen=True)
class SteelTransitionInstance:
    """Normalized input for a steel transition-sequencing model."""

    name: str
    coils: tuple[tuple[float, ...], ...] = ()
    penalty_matrix: tuple[tuple[int, ...], ...] | None = None

    @property
    def coil_count(self) -> int:
        if self.penalty_matrix is not None:
            return len(self.penalty_matrix)
        return len(self.coils)
@lru_cache(maxsize=1)


def load_steel_instances() -> dict[str, SteelTransitionInstance]:
    payload = json.loads(COIL_DATA_PATH.read_text(encoding="utf-8"))
    bundled = payload["bundled"]
    instances = {
        "toy": _coils_instance("toy", payload["toy"]),
        "bundled_head40": _coils_instance("bundled_head40", bundled[:40]),
        "bundled": _coils_instance("bundled", bundled),
        "sample303": _load_sample303(),
    }
    instances.update(_load_graph_instances(GRAPH900_DATA_PATH, prefix="graph900"))
    instances.update(_load_graph_instances(GRAPH1000_DATA_PATH, prefix="graph1000"))
    return instances


def _coils_instance(name: str, rows: list[list[float]]) -> SteelTransitionInstance:
    return SteelTransitionInstance(
        name=name,
        coils=tuple(tuple(float(value) for value in row) for row in rows),
    )


def _load_sample303() -> SteelTransitionInstance:
    payload = json.loads(SAMPLE303_DATA_PATH.read_text(encoding="utf-8"))
    rows = payload["coils"]
    if len(rows) != 303:
        raise ValueError("sample_303.json must contain exactly 303 coils")
    return _coils_instance("sample303", rows)


def _load_graph_instances(
    path: Path,
    *,
    prefix: str,
) -> dict[str, SteelTransitionInstance]:
    instances: dict[str, SteelTransitionInstance] = {}
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            payload = json.loads(line)
            graph_id = int(payload["graph_id"])
            node_count = int(payload["node_count"])
            name = f"{prefix}_{graph_id:02d}"
            instances[name] = SteelTransitionInstance(
                name=name,
                penalty_matrix=_penalty_matrix_from_compatible_edges(
                    node_count,
                    payload["edges"],
                ),
            )
    if len(instances) != 10:
        raise ValueError(f"{path.name} must contain exactly 10 graph instances")
    return instances


def _penalty_matrix_from_compatible_edges(
    node_count: int,
    edges: list[list[int]],
) -> tuple[tuple[int, ...], ...]:
    """Map an undirected compatible-edge list to the domain's 0/1 costs."""

    matrix = [[1] * node_count for _ in range(node_count)]
    for node in range(node_count):
        matrix[node][node] = 0
    for raw_left, raw_right in edges:
        left = int(raw_left)
        right = int(raw_right)
        if not 0 <= left < node_count or not 0 <= right < node_count or left == right:
            raise ValueError("graph edge endpoint is invalid")
        matrix[left][right] = 0
        matrix[right][left] = 0
    return tuple(tuple(row) for row in matrix)
