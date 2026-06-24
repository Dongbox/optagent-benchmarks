from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True)
class StrategyDeclaration:
    """Default public OptAgent strategy declaration for a benchmark case."""

    name: str
    config_class: str
    profile: str
    kind: str = "strategy_run"
    config: Mapping[str, Any] = field(default_factory=dict)
    notes: str | None = None

    def to_row(self) -> dict[str, Any]:
        row: dict[str, Any] = {
            "name": self.name,
            "config_class": self.config_class,
            "profile": self.profile,
            "kind": self.kind,
            "config": dict(self.config),
        }
        if self.notes is not None:
            row["notes"] = self.notes
        return row


@dataclass(frozen=True)
class BenchmarkCase:
    """Structured case declaration shared by cases, local entrypoints, and runners."""

    benchmark_id: str
    source: str
    problem_type: str
    instance_type: str
    instance: str
    family: str
    tier: str
    compare_key: str
    series_key: str
    size: Mapping[str, Any]
    data: Mapping[str, Any]
    reference: Mapping[str, Any]
    problem_description: str
    case_module: str
    modeling_notes: Mapping[str, Any] = field(default_factory=dict)
    default_strategies: tuple[StrategyDeclaration, ...] = ()
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> "BenchmarkCase":
        benchmark_id = str(row["benchmark_id"])
        instance = str(row.get("instance") or benchmark_id)
        family = str(row.get("family") or "")
        case_module = str(row.get("case_module") or "")
        source, problem_type, instance_type = _infer_case_path_parts(row, case_module)
        modeling_notes = _modeling_notes_from_row(row)
        default_strategies = _strategy_declarations_from_row(row)
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
            "default_strategies",
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
            default_strategies=default_strategies,
            extra=MappingProxyType(extra),
        )

    def to_row(self) -> dict[str, Any]:
        row = dict(self.extra)
        row.update(
            {
                "benchmark_id": self.benchmark_id,
                "case_module": self.case_module,
                "data": dict(self.data),
                "family": self.family,
                "instance": self.instance,
                "problem_description": self.problem_description,
                "reference": dict(self.reference),
                "size": dict(self.size),
                "source": self.source,
                "tier": self.tier,
                "problem_type": self.problem_type,
                "instance_type": self.instance_type,
                "compare_key": self.compare_key,
                "series_key": self.series_key,
            }
        )
        if self.modeling_notes:
            row["modeling_notes"] = dict(self.modeling_notes)
        if self.default_strategies:
            row["default_strategies"] = [strategy.to_row() for strategy in self.default_strategies]
            row["default_strategy_names"] = self.default_strategy_names()
        return row

    def load_instance(self, **kwargs: Any) -> Any:
        raise NotImplementedError(f"{type(self).__name__}.load_instance is not implemented")

    def build_model(self, instance_data: Any | None = None, **kwargs: Any) -> Any:
        raise NotImplementedError(f"{type(self).__name__}.build_model is not implemented")

    def default_strategy_names(self) -> tuple[str, ...]:
        return tuple(strategy.name for strategy in self.default_strategies)

    def strategy_config(self, name: str) -> Any:
        declaration = next((strategy for strategy in self.default_strategies if strategy.name == name), None)
        if declaration is None:
            raise KeyError(f"unknown default strategy for {self.benchmark_id}: {name}")
        config_class = _resolve_config_class(declaration.config_class)
        return config_class(**dict(declaration.config))

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


def _strategy_declarations_from_row(row: Mapping[str, Any]) -> tuple[StrategyDeclaration, ...]:
    values = row.get("default_strategies")
    if not isinstance(values, (tuple, list)):
        return ()
    strategies: list[StrategyDeclaration] = []
    for value in values:
        if isinstance(value, StrategyDeclaration):
            strategies.append(value)
        elif isinstance(value, Mapping):
            strategies.append(
                StrategyDeclaration(
                    name=str(value["name"]),
                    config_class=str(value["config_class"]),
                    profile=str(value.get("profile") or value["name"]),
                    kind=str(value.get("kind") or "strategy_run"),
                    config=_mapping(value.get("config")),
                    notes=str(value["notes"]) if value.get("notes") is not None else None,
                )
            )
    return tuple(strategies)


def _default_series_key(compare_key: str, modeling_notes: Mapping[str, Any]) -> str:
    model_style = modeling_notes.get("model_style")
    if model_style:
        return f"{compare_key}/{model_style}"
    return compare_key


def _resolve_config_class(config_class: str) -> Any:
    if "." in config_class:
        module_name, _, attr = config_class.rpartition(".")
        return getattr(import_module(module_name), attr)
    optagent = import_module("optagent")
    return getattr(optagent, config_class)
