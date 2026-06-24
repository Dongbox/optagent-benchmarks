from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from optagent import ExternalCallbackContext, ModelBuilder

from benchmarks.cases.base import BenchmarkCase

SOURCE = "QAPLIB"
SOURCE_KEY = "qaplib"
PROBLEM_TYPE = "assignment"
INSTANCE_TYPE = "quadratic_assignment"
FAMILY = "sequence_quadratic_assignment"
MODEL_STYLE = "sequence_var_external_call"
RAW_DIR = Path(__file__).resolve().parent / "raw"
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


class QapCase(BenchmarkCase):
    def build_model(self, **kwargs: Any) -> ModelBuilder:
        allow_download = bool(kwargs.get("allow_download", True))
        instance = load_qap_case(self.to_row(), cache_dir=RAW_DIR, allow_download=allow_download)
        default_assignment = list(range(instance.size))
        builder = ModelBuilder(metadata={"model_style": MODEL_STYLE})
        assignment = builder.sequence_var(size=instance.size, default=default_assignment, name="assignment")

        def assignment_cost(ctx: ExternalCallbackContext) -> int:
            candidate = [int(item) for item in ctx.value(assignment)]
            return instance.assignment_cost(candidate)

        builder.minimize(
            builder.external_call(
                assignment_cost,
                name="assignment_cost",
                pure=True,
                deterministic=True,
                cacheable=True,
                timeout_ms=100,
                depends_on=(assignment,),
            ),
            name="assignment_cost",
        )
        self._set_build_context({"instance": instance, "assignment_node_id": assignment.node_id})
        return builder

    def solution_metrics(self, solution: Any, **kwargs: Any) -> dict[str, Any]:
        context = self._build_context()
        instance = context["instance"]
        assignment_node_id = int(context["assignment_node_id"])
        assignment = [int(item) for item in solution.variable_values[assignment_node_id]]
        objective = instance.assignment_cost(assignment)
        reference = instance.reference_objective
        return {
            "objective": float(objective),
            "reference_objective": float(reference) if reference is not None else None,
            "decoded_solution": {
                "kind": "sequence",
                "sequence": assignment,
            },
            "model_style": MODEL_STYLE,
        }


def make_qap_case(
    *,
    benchmark_id: str,
    instance: str,
    tier: str,
    size: int,
    raw_path: str | Path,
    solution_raw_path: str | Path,
    objective: int,
    source_label: str,
    case_module: str,
    instance_url: str | None = None,
    solution_url: str | None = None,
) -> QapCase:
    compare_key = f"{SOURCE_KEY}/{PROBLEM_TYPE}/{INSTANCE_TYPE}/{instance}"
    data: dict[str, Any] = {
        "raw_path": str(raw_path),
        "solution_raw_path": str(solution_raw_path),
        "instance_page_url": f"{QAPLIB_ROOT}/",
        "solution_page_url": f"{QAPLIB_ROOT}/",
    }
    if instance_url is not None:
        data["instance_url"] = instance_url
    if solution_url is not None:
        data["solution_url"] = solution_url
    return QapCase(
        benchmark_id=benchmark_id,
        source=SOURCE,
        problem_type=PROBLEM_TYPE,
        instance_type=INSTANCE_TYPE,
        instance=instance,
        family=FAMILY,
        tier=tier,
        compare_key=compare_key,
        series_key=f"{compare_key}/{MODEL_STYLE}",
        size={"facilities": size, "locations": size},
        data=data,
        reference={
            "objective": objective,
            "source_label": source_label,
            "source_url": f"{QAPLIB_ROOT}/",
            "status": "optimal",
            "value_kind": "optimal",
        },
        problem_description=(
            f"QAPLIB quadratic assignment instance {instance}: assign {size} facilities to {size} "
            "locations. The cost is the sum of flow between facility pairs multiplied by distance "
            "between assigned locations. This is a permutation blackbox benchmark with a published optimum."
        ),
        case_module=case_module,
        modeling_notes={
            "model_style": MODEL_STYLE,
            "objective_sense": "minimize",
            "public_api_primitives": ["sequence_var", "external_call"],
        },
    )


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
    cache_dir: str | Path = RAW_DIR,
    allow_download: bool = True,
) -> QapInstance:
    data = case.get("data", {})
    instance_name = str(case.get("instance") or case["benchmark_id"].removeprefix("qaplib_"))
    local_path = data.get("local_path")
    if local_path:
        instance = parse_qaplib_dat(Path(local_path).read_text(encoding="utf-8"), name=instance_name)
    else:
        data_path = Path(str(data.get("raw_path") or "")) if data.get("raw_path") else Path(cache_dir) / f"{instance_name}.dat"
        data_text = _read_or_download(
            path=data_path,
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
            solution_path = (
                Path(str(data.get("solution_raw_path") or ""))
                if data.get("solution_raw_path")
                else Path(cache_dir) / f"{instance_name}.sln"
            )
            solution_text = _read_or_download(
                path=solution_path,
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
