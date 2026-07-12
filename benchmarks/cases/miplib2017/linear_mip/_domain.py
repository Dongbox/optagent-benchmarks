from __future__ import annotations

from dataclasses import dataclass
import gzip
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from optagent import ModelBuilder

from benchmarks.cases.base import BenchmarkCase, SolutionVerification

SOURCE = "MIPLIB 2017 benchmark-v2"
SOURCE_KEY = "miplib2017"
PROBLEM_TYPE = "exact"
INSTANCE_TYPE = "linear_mip"
FAMILY = "exact_linear_mip"
MODEL_STYLE = "mps_linear_mp"
RAW_DIR = Path(__file__).resolve().parent / "raw"
MIPLIB_INSTANCE_ROOT = "https://miplib.zib.de/WebData/instances"


@dataclass
class MpsVariableSpec:
    name: str
    lb: float | None = 0.0
    ub: float | None = None
    is_integer: bool = False
    is_binary: bool = False


@dataclass(frozen=True)
class MpsLinearConstraint:
    name: str
    sense: str
    terms: tuple[tuple[str, float], ...]
    rhs: float
    range_value: float | None = None


@dataclass(frozen=True)
class ParsedMpsInstance:
    name: str
    objective_row: str
    objective_sense: str
    objective_terms: tuple[tuple[str, float], ...]
    constraints: tuple[MpsLinearConstraint, ...]
    variables: dict[str, MpsVariableSpec]

    @property
    def variable_count(self) -> int:
        return len(self.variables)

    @property
    def binary_count(self) -> int:
        return sum(1 for spec in self.variables.values() if spec.is_binary)

    @property
    def integer_count(self) -> int:
        return sum(1 for spec in self.variables.values() if spec.is_integer and not spec.is_binary)

    @property
    def continuous_count(self) -> int:
        return self.variable_count - self.binary_count - self.integer_count

    @property
    def constraint_count(self) -> int:
        return len(self.constraints)

    @property
    def nonzero_count(self) -> int:
        return len(self.objective_terms) + sum(len(row.terms) for row in self.constraints)


class MipCase(BenchmarkCase):
    def build_model(self, **kwargs: Any) -> ModelBuilder:
        allow_download = bool(kwargs.get("allow_download", True))
        instance = load_miplib_case(self.to_row(), cache_dir=RAW_DIR, allow_download=allow_download)
        builder = ModelBuilder(metadata={"model_style": MODEL_STYLE})
        const_cache: dict[float, Any] = {}
        variable_exprs: dict[str, Any] = {}
        variable_node_ids: dict[str, int] = {}

        def const_expr(value: float) -> Any:
            normalized = float(value)
            expr = const_cache.get(normalized)
            if expr is None:
                expr = builder.const(normalized)
                const_cache[normalized] = expr
            return expr

        for name, spec in instance.variables.items():
            if spec.is_binary:
                expr = builder.bool_var(default=False, name=name)
            elif spec.is_integer:
                lb = _coerce_int_bound(spec.lb)
                ub = _coerce_int_bound(spec.ub)
                expr = builder.int_var(default=_default_for_integer(lb, ub), lb=lb, ub=ub, name=name)
            else:
                lb = None if spec.lb is None else float(spec.lb)
                ub = None if spec.ub is None else float(spec.ub)
                expr = builder.float_var(default=_default_for_float(lb, ub), lb=lb, ub=ub, name=name)
            variable_exprs[name] = expr
            variable_node_ids[name] = expr.node_id

        objective_expr = _weighted_sum(builder, const_expr, variable_exprs, instance.objective_terms)
        if instance.objective_sense == "max":
            builder.maximize(objective_expr, name=instance.objective_row)
        else:
            builder.minimize(objective_expr, name=instance.objective_row)

        for row in instance.constraints:
            _add_constraint(builder, const_expr, variable_exprs, row)
        self._set_build_context({"instance": instance, "variable_node_ids": variable_node_ids})
        return builder

    def solution_metrics(self, solution: Any, **kwargs: Any) -> dict[str, Any]:
        context = self._build_context()
        instance = context["instance"]
        objective = solution.objective_value if solution.feasible else None
        raw_objective = solution.objective_value
        return {
            "objective": float(objective) if objective is not None else None,
            "raw_objective": float(raw_objective) if raw_objective is not None else None,
            "model_style": MODEL_STYLE,
            "metadata": {
                **_exact_metadata(solution.diagnostics),
                "variables": instance.variable_count,
                "binary_variables": instance.binary_count,
                "integer_variables": instance.integer_count,
                "continuous_variables": instance.continuous_count,
                "constraints": instance.constraint_count,
                "nonzeros": instance.nonzero_count,
            },
        }

    def verify_solution(self, solution: Any, **kwargs: Any) -> SolutionVerification:
        context = self._build_context()
        instance = context["instance"]
        values: dict[str, float] = {}
        violations: list[str] = []
        tolerance = 1e-7
        for name, spec in instance.variables.items():
            node_id = context["variable_node_ids"][name]
            raw = solution.variable_values.get(node_id)
            if isinstance(raw, bool):
                value = float(int(raw))
            elif isinstance(raw, (int, float)):
                value = float(raw)
            else:
                violations.append(f"variable {name} has no numeric value")
                continue
            if spec.lb is not None and value < float(spec.lb) - tolerance:
                violations.append(f"variable {name} violates lower bound {spec.lb}")
            if spec.ub is not None and value > float(spec.ub) + tolerance:
                violations.append(f"variable {name} violates upper bound {spec.ub}")
            if spec.is_integer and abs(value - round(value)) > tolerance:
                violations.append(f"variable {name} must be integer")
            if spec.is_binary and min(abs(value), abs(value - 1.0)) > tolerance:
                violations.append(f"variable {name} must be binary")
            values[name] = value
        for row in instance.constraints:
            if any(name not in values for name, _coefficient in row.terms):
                violations.append(f"constraint {row.name} cannot be evaluated")
                continue
            lhs = sum(values[name] * coefficient for name, coefficient in row.terms)
            if row.range_value is not None:
                lower, upper = _range_bounds(row)
                if lower is not None and lhs < lower - tolerance:
                    violations.append(f"constraint {row.name} violates ranged lower bound")
                if upper is not None and lhs > upper + tolerance:
                    violations.append(f"constraint {row.name} violates ranged upper bound")
            elif row.sense == "L" and lhs > row.rhs + tolerance:
                violations.append(f"constraint {row.name} violates upper bound")
            elif row.sense == "G" and lhs < row.rhs - tolerance:
                violations.append(f"constraint {row.name} violates lower bound")
            elif row.sense == "E" and abs(lhs - row.rhs) > tolerance:
                violations.append(f"constraint {row.name} violates equality")
        if violations:
            return SolutionVerification.failed(*violations)
        objective = sum(values[name] * coefficient for name, coefficient in instance.objective_terms)
        return SolutionVerification.accepted(objective=float(objective))


def make_mip_case(
    *,
    benchmark_id: str,
    instance: str,
    tier: str,
    size: dict[str, int],
    raw_path: str | Path,
    objective: float,
    miplib_status: str,
    tags: tuple[str, ...],
    case_module: str,
) -> MipCase:
    compare_key = f"{SOURCE_KEY}/{PROBLEM_TYPE}/{INSTANCE_TYPE}/{instance}"
    tag_text = ", ".join(tags)
    return MipCase(
        benchmark_id=benchmark_id,
        source=SOURCE,
        problem_type=PROBLEM_TYPE,
        instance_type=INSTANCE_TYPE,
        instance=instance,
        family=FAMILY,
        tier=tier,
        compare_key=compare_key,
        series_key=f"{compare_key}/{MODEL_STYLE}",
        size=size,
        data={
            "raw_path": str(raw_path),
            "benchmark_list_url": "https://miplib.zib.de/downloads/benchmark-v2.test",
            "instance_archive_url": "https://miplib.zib.de/downloads/benchmark.zip",
            "instance_detail_url": f"https://miplib.zib.de/instance_details_{instance}.html",
            "solution_url": "https://miplib.zib.de/downloads/miplib2017-v36.solu",
        },
        reference={
            "download_page_url": "https://miplib.zib.de/download.html",
            "miplib_status": miplib_status,
            "notes": "Use as MP/exact-backend baseline, not as the primary GA/ALNS benchmark family.",
            "objective": objective,
            "source_url": "https://miplib.zib.de/downloads/miplib2017-v36.solu",
            "status": "opt",
            "tags": list(tags),
            "value_kind": "optimal",
        },
        problem_description=(
            f"MIPLIB 2017 benchmark instance {instance}: linear mixed-integer program with "
            f"{size.get('variables', 0)} variables, {size.get('constraints', 0)} constraints, "
            f"and tags [{tag_text}]. It is included as an exact MP/MPS backend benchmark rather "
            "than a primary GA/ALNS search case."
        ),
        case_module=case_module,
        modeling_notes={
            "model_style": MODEL_STYLE,
            "objective_sense": "minimize",
            "public_api_primitives": ["int_var", "bool_var", "float_var", "linear_constraints"],
        },
    )


def parse_mps_text(text: str, *, name: str | None = None, objective_sense: str = "min") -> ParsedMpsInstance:
    instance_name = name or "mps_instance"
    effective_objective_sense = objective_sense
    row_senses: dict[str, str] = {}
    row_terms: dict[str, list[tuple[str, float]]] = {}
    rhs_values: dict[str, float] = {}
    range_values: dict[str, float] = {}
    variables: dict[str, MpsVariableSpec] = {}
    objective_row: str | None = None
    objective_terms: list[tuple[str, float]] = []
    integer_mode = False
    section: str | None = None
    pending_objsense = False

    for raw_line in text.splitlines():
        line = raw_line.rstrip("\n")
        stripped = line.strip()
        if not stripped or stripped.startswith("*"):
            continue
        tokens = stripped.split()
        head = tokens[0].upper()
        is_section_header = not line[:1].isspace()

        if pending_objsense:
            if head in {"MIN", "MINIMIZE", "MINIMUM"}:
                effective_objective_sense = "min"
                pending_objsense = False
                continue
            if head in {"MAX", "MAXIMIZE", "MAXIMUM"}:
                effective_objective_sense = "max"
                pending_objsense = False
                continue
            pending_objsense = False

        if is_section_header and head == "OBJSENSE":
            section = head
            if len(tokens) > 1:
                effective_objective_sense = _parse_objective_sense(tokens[1])
            else:
                pending_objsense = True
            continue
        if is_section_header and head in {"NAME", "ROWS", "COLUMNS", "RHS", "RANGES", "BOUNDS", "ENDATA"}:
            section = head
            if head == "NAME" and len(tokens) >= 2:
                instance_name = tokens[1]
            if head == "ENDATA":
                break
            continue

        if section == "ROWS":
            if len(tokens) < 2:
                raise ValueError(f"invalid ROWS line: {line!r}")
            sense, row_name = tokens[0].upper(), tokens[1]
            row_senses[row_name] = sense
            if sense == "N" and objective_row is None:
                objective_row = row_name
            continue

        if section == "COLUMNS":
            if len(tokens) >= 2 and tokens[1].upper().strip("'") == "MARKER":
                marker = tokens[2].upper().strip("'") if len(tokens) >= 3 else ""
                if marker == "INTORG":
                    integer_mode = True
                    continue
                if marker == "INTEND":
                    integer_mode = False
                    continue
            var_name = tokens[0]
            spec = variables.setdefault(var_name, MpsVariableSpec(name=var_name))
            if integer_mode:
                spec.is_integer = True
            for index in range(1, len(tokens), 2):
                if index + 1 >= len(tokens):
                    break
                row_name = tokens[index]
                coefficient = float(tokens[index + 1])
                if row_name == objective_row:
                    objective_terms.append((var_name, coefficient))
                else:
                    row_terms.setdefault(row_name, []).append((var_name, coefficient))
            continue

        if section == "RHS":
            _read_named_value_pairs(tokens, rhs_values)
            continue

        if section == "RANGES":
            _read_named_value_pairs(tokens, range_values)
            continue

        if section == "BOUNDS":
            if len(tokens) < 3:
                continue
            bound_type = tokens[0].upper()
            var_name = tokens[2]
            value = float(tokens[3]) if len(tokens) > 3 else None
            spec = variables.setdefault(var_name, MpsVariableSpec(name=var_name))
            _apply_bound(spec, bound_type, value)
            continue

    if objective_row is None:
        raise ValueError("MPS objective row is required")

    constraints = []
    for row_name, sense in row_senses.items():
        if row_name == objective_row:
            continue
        constraints.append(
            MpsLinearConstraint(
                name=row_name,
                sense=sense,
                terms=tuple(row_terms.get(row_name, ())),
                rhs=float(rhs_values.get(row_name, 0.0)),
                range_value=range_values.get(row_name),
            )
        )
    return ParsedMpsInstance(
        name=instance_name,
        objective_row=objective_row,
        objective_sense=effective_objective_sense,
        objective_terms=tuple(objective_terms),
        constraints=tuple(constraints),
        variables=variables,
    )


def load_miplib_case(
    case: dict[str, Any],
    *,
    cache_dir: str | Path = RAW_DIR,
    allow_download: bool = True,
) -> ParsedMpsInstance:
    data = case.get("data", {})
    instance_name = str(case.get("instance") or case["benchmark_id"].removeprefix("miplib2017_"))
    local_path = data.get("local_path")
    if local_path:
        path = Path(local_path)
        text = _read_mps_path(path)
        return parse_mps_text(text, name=instance_name)

    path = (
        Path(str(data.get("raw_path") or "")) if data.get("raw_path") else Path(cache_dir) / f"{instance_name}.mps.gz"
    )
    if path.exists():
        return parse_mps_text(_read_mps_path(path), name=instance_name)

    urls = _case_urls(case, instance_name)
    if not allow_download:
        raise FileNotFoundError(f"cached MIPLIB file not found and downloads are disabled: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    for url in urls:
        try:
            raw = _download_bytes(url)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            errors.append(f"{url}: {type(exc).__name__}: {exc}")
            continue
        path.write_bytes(raw)
        return parse_mps_text(_read_mps_path(path), name=instance_name)
    raise RuntimeError(
        f"failed to download MIPLIB case {case['benchmark_id']} from {len(urls)} source(s): " + " | ".join(errors)
    )


def _add_constraint(
    builder: ModelBuilder, const_expr: Any, variable_exprs: dict[str, Any], row: MpsLinearConstraint
) -> None:
    lhs = _weighted_sum(builder, const_expr, variable_exprs, row.terms)
    rhs = const_expr(row.rhs)
    if row.range_value is None:
        if row.sense == "L":
            builder.constraint(lhs <= rhs, name=row.name)
            return
        if row.sense == "G":
            builder.constraint(lhs >= rhs, name=row.name)
            return
        if row.sense == "E":
            builder.constraint(lhs == rhs, name=row.name)
            return
    lb, ub = _range_bounds(row)
    if lb is not None:
        builder.constraint(lhs >= const_expr(lb), name=f"{row.name}_range_lb")
    if ub is not None:
        builder.constraint(lhs <= const_expr(ub), name=f"{row.name}_range_ub")


def _read_mps_path(path: Path) -> str:
    raw = path.read_bytes()
    if path.suffix == ".gz":
        raw = gzip.decompress(raw)
    return raw.decode("utf-8", errors="replace")


def _case_urls(case: dict[str, Any], instance_name: str) -> list[str]:
    data = case.get("data", {})
    return [
        str(url)
        for url in [
            data.get("instance_url"),
            *data.get("mirror_urls", []),
            f"{MIPLIB_INSTANCE_ROOT}/{instance_name}.mps.gz",
        ]
        if url
    ]


def _download_bytes(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "optagent-benchmark/1.0"})
    with urlopen(request, timeout=120) as response:
        return response.read()


def _read_named_value_pairs(tokens: list[str], target: dict[str, float]) -> None:
    for index in range(1, len(tokens), 2):
        if index + 1 >= len(tokens):
            break
        target[tokens[index]] = float(tokens[index + 1])


def _parse_objective_sense(raw: str) -> str:
    value = raw.strip().lower()
    if value in {"min", "minimize", "minimum"}:
        return "min"
    if value in {"max", "maximize", "maximum"}:
        return "max"
    raise ValueError(f"unsupported MPS objective sense: {raw}")


def _apply_bound(spec: MpsVariableSpec, bound_type: str, value: float | None) -> None:
    if bound_type == "UP":
        spec.ub = value
        return
    if bound_type == "LO":
        spec.lb = value
        return
    if bound_type == "FX":
        spec.lb = value
        spec.ub = value
        return
    if bound_type == "FR":
        spec.lb = None
        spec.ub = None
        return
    if bound_type == "MI":
        spec.lb = None
        return
    if bound_type == "PL":
        spec.ub = None
        return
    if bound_type == "BV":
        spec.is_integer = True
        spec.is_binary = True
        spec.lb = 0.0
        spec.ub = 1.0
        return
    if bound_type == "LI":
        spec.is_integer = True
        spec.lb = value
        return
    if bound_type == "UI":
        spec.is_integer = True
        spec.ub = value
        return
    raise ValueError(f"unsupported MPS bound type: {bound_type}")


def _range_bounds(row: MpsLinearConstraint) -> tuple[float | None, float | None]:
    if row.range_value is None:
        raise ValueError("range_value is required")
    rhs = float(row.rhs)
    span = abs(float(row.range_value))
    if row.sense == "L":
        return rhs - span, rhs
    if row.sense == "G":
        return rhs, rhs + span
    if row.sense == "E":
        if row.range_value >= 0:
            return rhs, rhs + span
        return rhs - span, rhs
    raise ValueError(f"unsupported row sense: {row.sense}")


def _weighted_sum(
    builder: ModelBuilder, const_expr: Any, variables: dict[str, Any], terms: tuple[tuple[str, float], ...]
) -> Any:
    if not terms:
        return const_expr(0.0)
    exprs: list[Any] = []
    for variable_name, coefficient in terms:
        variable = variables[variable_name]
        if coefficient == 1:
            exprs.append(variable)
        elif coefficient == -1:
            exprs.append(-variable)
        else:
            exprs.append(variable * const_expr(coefficient))
    if len(exprs) == 1:
        return exprs[0]
    return builder.sum(*exprs)


def _coerce_int_bound(value: float | None) -> int | None:
    if value is None:
        return None
    rounded = int(round(value))
    if abs(float(value) - rounded) > 1e-9:
        raise ValueError(f"expected integer bound, got {value}")
    return rounded


def _default_for_integer(lb: int | None, ub: int | None) -> int:
    if lb is not None and ub is not None and lb == ub:
        return lb
    if lb is not None and lb > 0:
        return lb
    if ub is not None and ub < 0:
        return ub
    return 0


def _default_for_float(lb: float | None, ub: float | None) -> float:
    if lb is not None and ub is not None and abs(lb - ub) <= 1e-12:
        return lb
    if lb is not None and lb > 0.0:
        return lb
    if ub is not None and ub < 0.0:
        return ub
    return 0.0


def _exact_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "backend",
        "solver_status",
        "status",
        "objective_value",
        "best_bound",
        "mip_gap",
        "simplex_iteration_count",
        "node_count",
        "constraint_violation_policy",
        "max_constraint_violation",
    )
    return {
        "mip_heuristic_route_enabled": False,
        "mip_heuristic_route_decision": "exact_only",
        "mip_heuristic_route_reason": "no_dedicated_milp_native_heuristic",
        "exact_baseline_required": True,
        **{key: metadata[key] for key in keys if key in metadata},
    }
