from __future__ import annotations

from dataclasses import dataclass
import gzip
import math
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


# TSPLIB TSP 数据说明：
# - 当前支持 selected symmetric TSP cases 需要的子集。
# - 坐标型实例读取 NODE_COORD_SECTION，并按 EDGE_WEIGHT_TYPE 计算 EUC_2D / CEIL_2D 距离。
# - 显式矩阵实例读取 EDGE_WEIGHT_SECTION，目前支持 FULL_MATRIX。
# - raw/ 保存已下载的公开原始文件；新增实例时优先把来源和格式写入 实例模块 与本文件注释。
# - loader 输出 TspInstance，系列模块可使用 external_call 黑盒距离目标，
#   也可使用 sequence_transition_sum 显式图目标。
DEFAULT_RAW_DIR = Path(__file__).resolve().parent


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


def parse_tsplib_text(text: str) -> TspInstance:
    """Parse the TSPLIB subset used by the selected symmetric TSP cases."""

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


def load_tsp_case(
    case: dict[str, Any],
    *,
    cache_dir: str | Path = DEFAULT_RAW_DIR,
    allow_download: bool = True,
) -> TspInstance:
    data = case.get("data", {})
    local_path = data.get("local_path")
    if local_path:
        return parse_tsplib_text(Path(local_path).read_text(encoding="utf-8"))

    instance_name = str(case.get("instance") or case["benchmark_id"].removeprefix("tsplib_"))
    path = Path(cache_dir) / f"{instance_name}.tsp"
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
            raw = _download_bytes(url)
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


def _download_bytes(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "optagent-benchmark/1.0"})
    with urlopen(request, timeout=60) as response:
        return response.read()
