from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Literal, Mapping

if TYPE_CHECKING:
    from optagent import ModelBuilder


VerificationStatus = Literal["passed", "failed", "unsupported"]


@dataclass(frozen=True)
class SolutionVerification:
    """Independent benchmark-side verification of a returned solution."""

    status: VerificationStatus
    passed: bool
    feasible: bool
    objective: float | None = None
    violations: tuple[str, ...] = ()

    @classmethod
    def accepted(cls, *, objective: float, feasible: bool = True) -> "SolutionVerification":
        return cls(status="passed", passed=True, feasible=feasible, objective=float(objective))

    @classmethod
    def failed(cls, *violations: str) -> "SolutionVerification":
        return cls(status="failed", passed=False, feasible=False, violations=tuple(violations))

    @classmethod
    def unsupported(cls) -> "SolutionVerification":
        return cls(status="unsupported", passed=False, feasible=False)


def verify_permutation(raw: Any, *, size: int, label: str) -> tuple[list[int] | None, tuple[str, ...]]:
    if not isinstance(raw, (list, tuple)):
        return None, (f"{label} must be a permutation sequence",)
    values = [_exact_int(item) for item in raw]
    if any(item is None for item in values):
        return None, (f"{label} must contain integer permutation members",)
    normalized = [int(item) for item in values if item is not None]
    if len(normalized) != size or set(normalized) != set(range(size)):
        return None, (f"{label} must be a permutation of 0..{size - 1}",)
    return normalized, ()


def verify_interval(raw: Any, *, duration: int, label: str) -> tuple[tuple[int, int] | None, tuple[str, ...]]:
    if not isinstance(raw, dict):
        return None, (f"{label} interval is missing",)
    start = _exact_int(raw.get("start"))
    end = _exact_int(raw.get("end"))
    length = _exact_int(raw.get("length"))
    if start is None or end is None or length is None:
        return None, (f"{label} interval must contain integer start/end/length",)
    if start < 0 or length != duration or end != start + duration:
        return None, (f"{label} interval is inconsistent with duration {duration}",)
    return (start, end), ()


def _exact_int(raw: Any) -> int | None:
    if isinstance(raw, bool):
        return int(raw)
    if isinstance(raw, int):
        return raw
    if isinstance(raw, float) and raw.is_integer():
        return int(raw)
    return None


@dataclass(frozen=True)
class BenchmarkCase:
    """不可变的基准测试用例：一个已知最优值的具体问题实例。

    该类是 case 声明、runner、dashboard 和本地入口点之间共享的核心契约。
    每个领域子类通过实现 :meth:`build_model` 来为该用例构建具体的 OptAgent 模型。

    本设计有意将传统 benchmark 拆分为 ``domain``（模型描述/问题类型元数据）和
    ``problem``（实例数据）的两层结构合为一体。领域级元数据作为字段存在于每个
    case 上（``source``、``problem_type``、``instance_type``、``family`` 等），
    由各子包的 ``_domain.py`` 中的工厂函数统一设置。实例特定数据在系列文件
    （如 ``j90_1.py``）中声明。

    当字段未显式填充时，``source`` / ``problem_type`` / ``instance_type`` 会
    通过 :func:`_infer_case_path_parts` 从模块路径推导。
    """

    benchmark_id: str
    """唯一标识符，如 ``"psplib_j90_1_1"``。"""

    family: str
    """问题族标签，如 ``"cumulative_resource_scheduling"``。"""

    size: Mapping[str, Any]
    """规模信息，如 ``{"activities": 90, "renewable_resources": 4}``。"""

    data: Mapping[str, Any]
    """实例文件路径/URL，可选的镜像 URL。"""

    reference: Mapping[str, Any]
    """已知最优解：``{"objective": 73, "status": "optimal"}``。"""

    problem_description: str
    """可读的实例一句话描述。"""

    source: str = ""
    """来源库或出处，如 ``"PSPLIB j90 via ScheduleOpt"``。"""

    problem_type: str = ""
    """广义问题类别，如 ``"scheduling"``。"""

    instance_type: str = ""
    """具体变体，如 ``"rcpsp"``。"""

    instance: str = ""
    """来源内的实例名称，如 ``"j90_1_1"``。"""

    tier: str = "smoke"
    """评估层级：``"smoke"`` | ``"calibration"`` | ``"full"`` | ``"pressure"``。"""

    compare_key: str = ""
    """层级分组键，如 ``"psplib/scheduling/rcpsp/j90_1_1"``。"""

    series_key: str = ""
    """时序聚合键，通常为 ``compare_key/model_style``。"""

    case_module: str = ""
    """声明该 case 的系列文件的 Python 点分隔模块路径。"""

    modeling_notes: Mapping[str, Any] = field(default_factory=dict)
    """模型风格、目标方向、使用的 API 原语。"""

    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)
    """额外结构化元数据（预算、策略建议等）。"""

    def verify_solution(self, solution: Any, **kwargs: Any) -> SolutionVerification:
        """Verify a returned candidate without trusting solver feasibility or objective facts."""

        return SolutionVerification.unsupported()

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

    def solution_metrics(self, solution: Any, **kwargs: Any) -> dict[str, Any]:
        return self.default_solution_metrics(solution)

    def solution_summary(self, solution: Any, **kwargs: Any) -> dict[str, Any]:
        return self.solution_metrics(solution, **kwargs)

    def default_solution_metrics(self, solution: Any) -> dict[str, Any]:
        return {}

    def _set_build_context(self, context: Mapping[str, Any]) -> None:
        object.__setattr__(self, "_last_build_context", dict(context))

    def _build_context(self) -> dict[str, Any]:
        context = getattr(self, "_last_build_context", None)
        if not isinstance(context, dict):
            raise RuntimeError(f"{type(self).__name__}.build_model must be called before solution_metrics")
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
    for key in ("objective_sense", "model_style"):
        if key in row:
            notes[key] = row[key]
    return MappingProxyType(notes)


def _default_series_key(compare_key: str, modeling_notes: Mapping[str, Any]) -> str:
    model_style = modeling_notes.get("model_style")
    if model_style:
        return f"{compare_key}/{model_style}"
    return compare_key
