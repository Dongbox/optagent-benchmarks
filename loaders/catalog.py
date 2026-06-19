from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG_PATH = REPO_ROOT / "benchmarks" / "catalog" / "modeling-native-catalog-v1.json"


def load_catalog(path: str | Path = DEFAULT_CATALOG_PATH) -> dict[str, Any]:
    """Load a modeling-native benchmark catalog."""

    return json.loads(Path(path).read_text(encoding="utf-8"))


def catalog_cases(path: str | Path = DEFAULT_CATALOG_PATH) -> list[dict[str, Any]]:
    return list(load_catalog(path)["cases"])


def select_cases(
    cases: Iterable[dict[str, Any]],
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
        if family_filter and case.get("family") not in family_filter:
            continue
        if tier_filter and case.get("tier") not in tier_filter:
            continue
        if id_filter and case.get("benchmark_id") not in id_filter:
            continue
        selected.append(case)
    return selected


def case_by_id(path: str | Path, benchmark_id: str) -> dict[str, Any]:
    for case in catalog_cases(path):
        if case["benchmark_id"] == benchmark_id:
            return case
    raise KeyError(f"catalog case not found: {benchmark_id}")
