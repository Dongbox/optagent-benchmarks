from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


# QAPLIB 数据说明：
# - `.dat` 文件第一项是规模 n，之后依次给出 n*n flow matrix 和 n*n distance matrix。
# - `.sln` 文件通常给出 reference objective 和 1-based assignment。
# - raw/ 保存已下载的公开原始文件；新增实例时优先把来源和格式写入 实例模块 与本文件注释。
# - loader 会读取 `.dat`，尽量读取 `.sln`，并把 assignment 转为 0-based。
# - 系列模块用一个 sequence_var 表示 facility -> location 的排列，用 external_call 计算二次费用。
DEFAULT_RAW_DIR = Path(__file__).resolve().parent
QAPLIB_ROOT = "https://qaplib.mgi.polymtl.ca"


@dataclass(frozen=True)
class QapInstance:
    name: str
    size: int
    flow: tuple[tuple[int, ...], ...]
    distance: tuple[tuple[int, ...], ...]
    reference_assignment: tuple[int, ...] = ()
    reference_objective: int | None = None

    def assignment_cost(self, assignment: list[int] | tuple[int, ...]) -> int:
        if len(assignment) != self.size:
            raise ValueError(f"assignment length {len(assignment)} does not match size {self.size}")
        if set(assignment) != set(range(self.size)):
            raise ValueError("assignment must be a permutation of all location ids")
        total = 0
        for left in range(self.size):
            left_location = int(assignment[left])
            for right in range(self.size):
                total += self.flow[left][right] * self.distance[left_location][int(assignment[right])]
        return int(total)


def parse_qaplib_dat(text: str, *, name: str) -> QapInstance:
    values = [int(item) for item in text.split()]
    if not values:
        raise ValueError("QAPLIB data is empty")
    size = values[0]
    expected = 1 + (2 * size * size)
    if len(values) != expected:
        raise ValueError(f"expected {expected} integer tokens for QAPLIB size {size}, found {len(values)}")
    matrix_values = values[1:]
    flow = tuple(
        tuple(matrix_values[row * size + col] for col in range(size))
        for row in range(size)
    )
    offset = size * size
    distance = tuple(
        tuple(matrix_values[offset + row * size + col] for col in range(size))
        for row in range(size)
    )
    return QapInstance(name=name, size=size, flow=flow, distance=distance)


def parse_qaplib_solution(text: str) -> tuple[int | None, tuple[int, ...]]:
    values = [int(item) for item in text.split()]
    if len(values) < 2:
        return None, tuple()
    size, objective = values[0], values[1]
    assignment = tuple(item - 1 for item in values[2 : 2 + size])
    return int(objective), assignment


def load_qap_case(
    case: dict[str, Any],
    *,
    cache_dir: str | Path = DEFAULT_RAW_DIR,
    allow_download: bool = True,
) -> QapInstance:
    data = case.get("data", {})
    instance_name = str(case.get("instance") or case["benchmark_id"].removeprefix("qaplib_"))
    local_path = data.get("local_path")
    if local_path:
        instance = parse_qaplib_dat(Path(local_path).read_text(encoding="utf-8"), name=instance_name)
    else:
        data_text = _read_or_download(
            path=Path(cache_dir) / f"{instance_name}.dat",
            urls=_case_data_urls(case, instance_name),
            allow_download=allow_download,
            benchmark_id=case["benchmark_id"],
        )
        instance = parse_qaplib_dat(data_text, name=instance_name)

    solution_text: str | None = None
    local_solution_path = data.get("local_solution_path")
    if local_solution_path:
        solution_text = Path(local_solution_path).read_text(encoding="utf-8")
    else:
        try:
            solution_text = _read_or_download(
                path=Path(cache_dir) / f"{instance_name}.sln",
                urls=_case_solution_urls(case, instance_name),
                allow_download=allow_download,
                benchmark_id=case["benchmark_id"],
            )
        except FileNotFoundError:
            solution_text = None
        except RuntimeError:
            solution_text = None

    reference_objective = case.get("reference", {}).get("objective")
    reference_assignment: tuple[int, ...] = ()
    if solution_text is not None:
        parsed_objective, reference_assignment = parse_qaplib_solution(solution_text)
        if parsed_objective is not None:
            reference_objective = parsed_objective

    return QapInstance(
        name=instance.name,
        size=instance.size,
        flow=instance.flow,
        distance=instance.distance,
        reference_assignment=reference_assignment,
        reference_objective=int(reference_objective) if reference_objective is not None else None,
    )


def _case_data_urls(case: dict[str, Any], instance_name: str) -> list[str]:
    data = case.get("data", {})
    return [
        str(url)
        for url in [
            data.get("instance_url"),
            *data.get("mirror_urls", []),
            f"{QAPLIB_ROOT}/data.d/{instance_name}.dat",
        ]
        if url
    ]


def _case_solution_urls(case: dict[str, Any], instance_name: str) -> list[str]:
    data = case.get("data", {})
    return [
        str(url)
        for url in [
            data.get("solution_url"),
            *data.get("solution_mirror_urls", []),
            f"{QAPLIB_ROOT}/soln.d/{instance_name}.sln",
        ]
        if url
    ]


def _read_or_download(
    *,
    path: Path,
    urls: list[str],
    allow_download: bool,
    benchmark_id: str,
) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    if not allow_download:
        raise FileNotFoundError(f"cached QAPLIB file not found and downloads are disabled: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    for url in urls:
        try:
            text = _download_text(url)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            errors.append(f"{url}: {type(exc).__name__}: {exc}")
            continue
        path.write_text(text, encoding="utf-8")
        return text
    raise RuntimeError(
        f"failed to download QAPLIB case {benchmark_id} from {len(urls)} source(s): "
        + " | ".join(errors)
    )


def _download_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": "optagent-benchmark/1.0"})
    with urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", errors="replace")
