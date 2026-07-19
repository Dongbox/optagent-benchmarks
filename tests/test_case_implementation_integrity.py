from __future__ import annotations

import importlib
from pathlib import Path
import re
from typing import Any

from benchmarks.cases.base import case_to_row
from benchmarks.cases.registry import benchmark_cases, run_case


REQUIRED_SMOKE_CASES = {
    "custom_steel_sequence_toy",
    "jsplib_ft06",
    "miplib2017_50v-10",
    "psplib_j30_1_4",
    "qaplib_nug12",
    "tsplib_berlin52",
}


def _cases_by_module() -> dict[str, list[dict[str, Any]]]:
    cases: dict[str, list[dict[str, Any]]] = {}
    for case in benchmark_cases():
        cases.setdefault(str(case["case_module"]), []).append(case)
    return cases


def test_public_case_inventory_and_metadata_are_consistent() -> None:
    cases = benchmark_cases()
    benchmark_ids = {case["benchmark_id"] for case in cases}
    assert cases
    assert len(benchmark_ids) == len(cases)
    assert REQUIRED_SMOKE_CASES <= benchmark_ids

    for case in cases:
        instance = str(case["instance"])
        assert instance
        assert str(case["case_module"]).startswith("benchmarks.cases.")
        assert str(case["benchmark_id"]).endswith(instance.replace("_", "-")) or str(case["benchmark_id"]).endswith(
            instance.replace("-", "_")
        )
        assert instance in str(case["compare_key"])
        assert str(case["series_key"]).startswith(f"{case['compare_key']}/")
        assert instance in str(case["series_key"])
        assert case.get("size")
        assert case.get("reference")
        assert case.get("problem_description")
        assert case.get("modeling_notes")


def test_case_module_points_to_module_that_declares_the_case() -> None:
    for module_name, cases in _cases_by_module().items():
        module = importlib.import_module(module_name)
        declared = {case_to_row(case)["benchmark_id"]: case_to_row(case) for case in module.CASES}

        assert module.CASE_MODULE == module.__name__
        assert set(declared) == {case["benchmark_id"] for case in cases}
        for case in cases:
            assert declared[case["benchmark_id"]]["case_module"] == module.__name__


def test_case_modules_do_not_reference_unrelated_public_instances() -> None:
    cases_by_module = _cases_by_module()
    all_instances = {case["instance"] for cases in cases_by_module.values() for case in cases}

    for module_name, cases in cases_by_module.items():
        module = importlib.import_module(module_name)
        module_path = Path(module.__file__).resolve()
        source = module_path.read_text(encoding="utf-8")
        allowed_instances = {case["instance"] for case in cases}

        for unrelated_instance in sorted(all_instances - allowed_instances):
            pattern = rf"(?<![A-Za-z0-9_-]){re.escape(unrelated_instance)}(?![A-Za-z0-9_-])"
            assert re.search(pattern, source) is None, (
                f"{module_path} references unrelated instance {unrelated_instance}"
            )


def test_registry_routes_each_case_to_unified_runner(monkeypatch: Any) -> None:
    import benchmarks.run as run_module

    for case in benchmark_cases():
        calls: list[str] = []

        def fake_run_benchmark_case(case_obj: Any, **_: Any) -> list[dict[str, Any]]:
            calls.append(case_obj.instance)
            return [{"benchmark_id": case_obj.benchmark_id, "instance": case_obj.instance}]

        monkeypatch.setattr(run_module, "run_benchmark_case", fake_run_benchmark_case)

        rows = run_case(case, allow_download=False)

        assert calls == [case["instance"]]
        assert rows == [{"benchmark_id": case["benchmark_id"], "instance": case["instance"]}]


def test_case_sources_do_not_reintroduce_legacy_runner_contracts() -> None:
    forbidden_patterns = (
        "class TspBenchmarkModel",
        "class QapBenchmarkModel",
        "class MipBenchmarkModel",
        "class JobShopBenchmarkModel",
        "class RcpspBenchmarkModel",
        "def load_instance",
        "def _load_instance",
        "def _build_model",
        "def _build_blackbox_model",
        "def _build_graph_model",
        "def solve_case",
        "StrategyDeclaration",
        "default_strategies",
    )
    for path in Path("benchmarks/cases").rglob("*.py"):
        if path.name == "base.py":
            continue
        source = path.read_text(encoding="utf-8")
        for pattern in forbidden_patterns:
            assert pattern not in source, f"{path} contains legacy case contract pattern: {pattern}"


def test_case_data_logic_stays_with_family_common_modules() -> None:
    data_modules = sorted(Path("benchmarks/cases").glob("**/raw/data.py"))
    assert data_modules == []


def test_legacy_root_scoring_entrypoints_stay_removed() -> None:
    removed_paths = [
        "run_collector.py",
        "run_scored_suite.py",
        "scoring.py",
        "scoring_phase2.py",
        "策略评分.md",
        "评估框架.md",
        "docs/phase2-plan.md",
    ]
    for path in removed_paths:
        assert not Path(path).exists(), f"{path} must not be reintroduced"
