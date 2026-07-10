from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any

from benchmarks.cases.base import BenchmarkCase, CaseDeclaration, case_to_row


# 这里登记的是“系列集合包”，每个包只汇总同一来源/业务域/问题类型下的
# 系列模块，例如 jsplib/scheduling/jobshop/abz.py。
INSTANCE_COLLECTION_MODULES = (
    "benchmarks.cases.custom.steel_transition_sequence",
    "benchmarks.cases.fjsplib.fjobshop",
    "benchmarks.cases.jsplib.jobshop",
    "benchmarks.cases.psplib.rcpsp",
    "benchmarks.cases.tsplib.tsp",
    "benchmarks.cases.qaplib.quadratic_assignment",
    "benchmarks.cases.miplib2017.linear_mip",
)

IMPLEMENTED_FAMILY_NAMES = {
    "cumulative_resource_scheduling",
    "exact_linear_mip",
    "flexible_interval_job_shop",
    "interval_job_shop",
    "sequence_transition_penalty",
    "sequence_blackbox_tsp",
    "sequence_quadratic_assignment",
}


def benchmark_cases() -> list[dict[str, Any]]:
    """从具体实例模块收集 case 声明。

    实例描述、数据来源、规模、reference 和默认 solve 入口都跟随系列文件；
    benchmark runner 只读取这些声明并按评估目的选择策略和预算。
    本函数返回 runner 兼容的 dict rows。
    """

    cases: list[dict[str, Any]] = []
    for module_name in INSTANCE_COLLECTION_MODULES:
        module = import_module(module_name)
        cases.extend(case_to_row(case) for case in getattr(module, "CASES"))
    return cases


def benchmark_case_objects() -> list[BenchmarkCase]:
    cases: list[BenchmarkCase] = []
    for module_name in INSTANCE_COLLECTION_MODULES:
        module = import_module(module_name)
        cases.extend(getattr(module, "CASES"))
    return cases


def case_module_for(case: CaseDeclaration) -> ModuleType:
    row = case_to_row(case)
    module_name = str(row.get("case_module") or "")
    if not module_name:
        raise KeyError(f"benchmark case is missing case_module: {row.get('benchmark_id')}")
    return import_module(module_name)


def run_case(case: CaseDeclaration, **kwargs: Any) -> list[dict[str, Any]]:
    """Run a case through the unified benchmarks.run entrypoint."""

    from benchmarks.run import run_benchmark_case

    row = case_to_row(case)
    selected = next((item for item in benchmark_case_objects() if item.benchmark_id == row["benchmark_id"]), None)
    if selected is None:
        raise KeyError(f"benchmark case not found: {row.get('benchmark_id')}")
    return run_benchmark_case(selected, **kwargs)


def default_model_styles_for_family(family: str) -> tuple[str, ...]:
    if family == "sequence_blackbox_tsp":
        from benchmarks.cases.tsplib.tsp.pr import DEFAULT_TSP_MODEL_STYLES

        return DEFAULT_TSP_MODEL_STYLES
    return ()


def implemented_families() -> set[str]:
    return set(IMPLEMENTED_FAMILY_NAMES)

