from __future__ import annotations

from typing import Any, Iterable

from benchmarks.cases.base import CaseDeclaration, case_to_row
from benchmarks.cases.registry import benchmark_cases


def all_cases() -> list[dict[str, Any]]:
    """从具体实例模块收集 benchmark case。

    case 元数据由具体实例模块承载；每个实例模块负责声明自己的
    数据来源、规模、reference 和默认求解入口。
    """

    return benchmark_cases()


def select_cases(
    cases: Iterable[CaseDeclaration],
    *,
    families: Iterable[str] | None = None,
    tiers: Iterable[str] | None = None,
    benchmark_ids: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    family_filter = set(families or ())
    tier_filter = set(tiers or ())
    id_filter = set(benchmark_ids or ())

    selected: list[dict[str, Any]] = []
    for case in cases:
        row = case_to_row(case)
        if family_filter and row.get("family") not in family_filter:
            continue
        if tier_filter and row.get("tier") not in tier_filter:
            continue
        if id_filter and row.get("benchmark_id") not in id_filter:
            continue
        selected.append(row)
    return selected


def case_by_id(benchmark_id: str) -> dict[str, Any]:
    for case in all_cases():
        if case["benchmark_id"] == benchmark_id:
            return case
    raise KeyError(f"benchmark case not found: {benchmark_id}")
