from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Mapping

if TYPE_CHECKING:
    from optagent import ModelBuilder


@dataclass(frozen=True)
class BenchmarkCase:
    """Structured case declaration shared by cases, local entrypoints, and runners."""

    benchmark_id: str
    family: str
    size: Mapping[str, Any]
    data: Mapping[str, Any]
    reference: Mapping[str, Any]
    problem_description: str
    source: str = ""
    problem_type: str = ""
    instance_type: str = ""
    instance: str = ""
    tier: str = "smoke"
    compare_key: str = ""
    series_key: str = ""
    case_module: str = ""
    modeling_notes: Mapping[str, Any] = field(default_factory=dict)
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> "BenchmarkCase":
        benchmark_id = str(row["benchmark_id"])
        instance = str(row.get("instance") or benchmark_id)
        family = str(row.get("family") or "")
        case_module = str(row.get("case_module") or "")
        source, problem_type, instance_type = _infer_case_path_parts(row, case_module)
        modeling_notes = _modeling_notes_from_row(row)
        compare_key = str(
            row.get("compare_key")
            or "/".join(part for part in (source, problem_type, instance_type, instance) if part)
            or benchmark_id
        )
        series_key = str(row.get("series_key") or _default_series_key(compare_key, modeling_notes))
        known_keys = {
            "benchmark_id",
            "source",
            "problem_type",
            "instance_type",
            "instance",
            "family",
            "tier",
            "compare_key",
            "series_key",
            "size",
            "data",
            "reference",
            "problem_description",
            "case_module",
            "modeling_notes",
        }
        extra = {key: value for key, value in row.items() if key not in known_keys}
        return cls(
            benchmark_id=benchmark_id,
            source=str(row.get("source") or source),
            problem_type=str(row.get("problem_type") or problem_type),
            instance_type=str(row.get("instance_type") or instance_type),
            instance=instance,
            family=family,
            tier=str(row.get("tier") or "smoke"),
            compare_key=compare_key,
            series_key=series_key,
            size=_mapping(row.get("size")),
            data=_mapping(row.get("data")),
            reference=_mapping(row.get("reference")),
            problem_description=str(row.get("problem_description") or ""),
            case_module=case_module,
            modeling_notes=modeling_notes,
            extra=MappingProxyType(extra),
        )

    def to_row(self) -> dict[str, Any]:
        source = self.source
        problem_type = self.problem_type
        instance_type = self.instance_type
        instance = self.instance or self.benchmark_id
        compare_key = self.compare_key or "/".join(
            part for part in (source, problem_type, instance_type, instance) if part
        )
        series_key = self.series_key or _default_series_key(compare_key, self.modeling_notes)
        row = dict(self.extra)
        row.update(
            {
                "benchmark_id": self.benchmark_id,
                "case_module": self.case_module,
                "data": dict(self.data),
                "family": self.family,
                "instance": instance,
                "problem_description": self.problem_description,
                "reference": dict(self.reference),
                "size": dict(self.size),
                "source": source,
                "tier": self.tier or "smoke",
                "problem_type": problem_type,
                "instance_type": instance_type,
                "compare_key": compare_key or self.benchmark_id,
                "series_key": series_key or (compare_key or self.benchmark_id),
            }
        )
        if self.modeling_notes:
            row["modeling_notes"] = dict(self.modeling_notes)
        return row

    def build_model(self, **kwargs: Any) -> "ModelBuilder":
        raise NotImplementedError(f"{type(self).__name__}.build_model is not implemented")

    def solution_summary(self, solution: Any, **kwargs: Any) -> dict[str, Any]:
        return self.default_solution_summary(solution)

    def default_solution_summary(self, solution: Any) -> dict[str, Any]:
        return {
            "solver_name": getattr(solution, "solver_name", None),
            "status": getattr(getattr(solution, "status", None), "value", str(getattr(solution, "status", ""))),
            "feasible": bool(getattr(solution, "feasible", False)),
            "objective": getattr(solution, "objective_value", None),
            "metadata": dict(getattr(solution, "metadata", {}) or {}),
        }

    def _set_build_context(self, context: Mapping[str, Any]) -> None:
        object.__setattr__(self, "_last_build_context", dict(context))

    def _build_context(self) -> dict[str, Any]:
        context = getattr(self, "_last_build_context", None)
        if not isinstance(context, dict):
            raise RuntimeError(f"{type(self).__name__}.build_model must be called before solution_summary")
        return context

    def reference_objective(self) -> float | None:
        for key in ("objective", "cost", "upper_bound", "lower_bound"):
            value = self.reference.get(key)
            if value is not None:
                try:
                    return float(value)
                except (TypeError, ValueError):
                    return None
        return None


CaseDeclaration = BenchmarkCase | Mapping[str, Any]


def ensure_benchmark_case(case: CaseDeclaration) -> BenchmarkCase:
    if isinstance(case, BenchmarkCase):
        return case
    return BenchmarkCase.from_mapping(case)


def case_to_row(case: CaseDeclaration) -> dict[str, Any]:
    if isinstance(case, BenchmarkCase):
        return case.to_row()
    return BenchmarkCase.from_mapping(case).to_row()


def _mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return MappingProxyType(dict(value))
    return MappingProxyType({})


def _infer_case_path_parts(row: Mapping[str, Any], case_module: str) -> tuple[str, str, str]:
    parts = case_module.split(".")
    if "cases" in parts:
        index = parts.index("cases")
        tail = parts[index + 1 :]
        if len(tail) >= 4:
            return tail[0], tail[1], tail[2]
    source = str(row.get("source") or "")
    return source, str(row.get("problem_type") or ""), str(row.get("instance_type") or row.get("family") or "")


def _modeling_notes_from_row(row: Mapping[str, Any]) -> Mapping[str, Any]:
    explicit = row.get("modeling_notes")
    if isinstance(explicit, Mapping):
        return MappingProxyType(dict(explicit))
    notes: dict[str, Any] = {}
    for key in ("modeling_form", "objective_sense", "optagent_primitives", "model_style"):
        if key in row:
            notes[key] = row[key]
    return MappingProxyType(notes)


def _default_series_key(compare_key: str, modeling_notes: Mapping[str, Any]) -> str:
    model_style = modeling_notes.get("model_style")
    if model_style:
        return f"{compare_key}/{model_style}"
    return compare_key
