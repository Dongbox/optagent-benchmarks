from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any


PACKAGE_PARENT = Path(__file__).resolve().parents[2]
if str(PACKAGE_PARENT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_PARENT))

from benchmarks.cases.base import case_to_row
from benchmarks.cases.registry import benchmark_cases, run_case


EXPECTED_CASE_COUNT = 29


def _cases_by_module() -> dict[str, list[dict[str, Any]]]:
    cases: dict[str, list[dict[str, Any]]] = {}
    for case in benchmark_cases():
        cases.setdefault(str(case["case_module"]), []).append(case)
    return cases


def test_public_case_inventory_and_metadata_are_consistent() -> None:
    cases = benchmark_cases()
    assert len(cases) == EXPECTED_CASE_COUNT
    assert len({case["benchmark_id"] for case in cases}) == EXPECTED_CASE_COUNT

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
            assert unrelated_instance not in source, f"{module_path} references unrelated instance {unrelated_instance}"


def test_registry_routes_each_case_to_its_own_module_with_instance(monkeypatch: Any) -> None:
    for case in benchmark_cases():
        module = importlib.import_module(str(case["case_module"]))
        calls: list[str] = []

        def fake_solve_case(instance: str, **_: Any) -> list[dict[str, Any]]:
            calls.append(instance)
            return [{"benchmark_id": case["benchmark_id"], "instance": instance}]

        monkeypatch.setattr(module, "solve_case", fake_solve_case)

        rows = run_case(case, allow_download=False)

        assert calls == [case["instance"]]
        assert rows == [{"benchmark_id": case["benchmark_id"], "instance": case["instance"]}]
