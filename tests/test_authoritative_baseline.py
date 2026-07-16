from __future__ import annotations

import json

import pytest

from benchmarks.authority import (
    HEURISTIC_SEEDS,
    RELEASE_GATE_PLAN,
    AuthorityInputs,
    assess_authority,
    assess_capabilities,
    case_lifecycle,
    case_lifecycle_inventory,
    iter_run_coordinates,
)
from benchmarks.run import LocalRunBudget, build_strategy_config, case_object_by_id
from benchmarks.authoritative_baseline import (
    PlannedRun,
    _backend_identity,
    _data_checksums,
    _install_wheel_environment,
    _memory_limiter,
    _platform_coordinate,
    build_run_command,
    planned_runs,
    main as authority_main,
)


def test_release_gate_plan_covers_supported_families_routes_and_tsp_styles() -> None:
    families = {entry.family for entry in RELEASE_GATE_PLAN}
    tsp_styles = {
        style for entry in RELEASE_GATE_PLAN if entry.family == "sequence_blackbox_tsp" for style in entry.model_styles
    }

    assert families == {
        "cumulative_resource_scheduling",
        "exact_linear_mip",
        "flexible_interval_job_shop",
        "interval_job_shop",
        "sequence_blackbox_tsp",
        "sequence_quadratic_assignment",
        "sequence_transition_penalty",
    }
    assert HEURISTIC_SEEDS == (11, 23, 47)
    assert tsp_styles == {
        "sequence_var_external_call",
        "sequence_var_sequence_transition_sum",
    }
    assert any(entry.strategies == ("optx",) and entry.seeds == (0,) for entry in RELEASE_GATE_PLAN)


def test_authority_requires_clean_provenance_complete_matrix_and_verified_rows() -> None:
    rows = [
        {
            "run_key": coordinate.run_key,
            "benchmark_id": coordinate.benchmark_id,
            "family": coordinate.family,
            "model_style": coordinate.model_style,
            "solve_route": coordinate.solve_route,
            "strategy": coordinate.strategy,
            "seed": coordinate.seed,
            "thread_count": coordinate.thread_count,
            "platform": _platform_coordinate(),
            "backend_name": "highs" if coordinate.solve_route == "embedded_highs" else "optagent_native_search",
            "backend_version": "1.14.0" if coordinate.solve_route == "embedded_highs" else "1.2.0rc1",
            "status": "feasible",
            "feasible": True,
            "verification_status": "passed",
            "verification_passed": True,
        }
        for coordinate in iter_run_coordinates()
    ]
    evidence_checksums = {
        **{f"{entry.benchmark_id}:reference": "sha256:" + "d" * 64 for entry in RELEASE_GATE_PLAN},
        **{f"{entry.benchmark_id}:instance:raw_path": "sha256:" + "e" * 64 for entry in RELEASE_GATE_PLAN},
    }
    accepted = assess_authority(
        AuthorityInputs(
            optagent_commit="a" * 40,
            benchmarks_commit="b" * 40,
            wheel_sha256="sha256:" + "c" * 64,
            optagent_dirty=False,
            benchmarks_dirty=False,
        ),
        rows,
        evidence_checksums=evidence_checksums,
    )
    dirty = assess_authority(
        AuthorityInputs(
            optagent_commit="a" * 40,
            benchmarks_commit="b" * 40,
            wheel_sha256="sha256:" + "c" * 64,
            optagent_dirty=True,
            benchmarks_dirty=False,
        ),
        rows,
        evidence_checksums=evidence_checksums,
    )
    incomplete = assess_authority(accepted.inputs, rows[:-1], evidence_checksums=evidence_checksums)
    unverified_rows = [dict(row) for row in rows]
    unverified_rows[0]["verification_passed"] = False
    unverified_rows[0]["verification_status"] = "not_run"
    unverified = assess_authority(accepted.inputs, unverified_rows, evidence_checksums=evidence_checksums)
    missing_checksum = assess_authority(
        accepted.inputs,
        rows,
        evidence_checksums={key: value for key, value in evidence_checksums.items() if key != "jsplib_ft06:reference"},
    )
    missing_backend_rows = [dict(row) for row in rows]
    del missing_backend_rows[0]["backend_version"]
    missing_backend = assess_authority(
        accepted.inputs,
        missing_backend_rows,
        evidence_checksums=evidence_checksums,
    )
    fallback_rows = [dict(row) for row in rows]
    fallback_rows[0]["fallback_attempts"] = 1
    fallback = assess_authority(accepted.inputs, fallback_rows, evidence_checksums=evidence_checksums)

    assert accepted.status == "authoritative"
    assert accepted.reasons == ()
    assert dirty.status == "non_authoritative"
    assert "optagent checkout is dirty" in dirty.reasons
    assert incomplete.status == "non_authoritative"
    assert any(reason.startswith("missing planned runs:") for reason in incomplete.reasons)
    assert unverified.status == "non_authoritative"
    assert any("independent verification" in reason for reason in unverified.reasons)
    assert missing_checksum.status == "non_authoritative"
    assert "missing evidence checksums: jsplib_ft06:reference" in missing_checksum.reasons
    assert missing_backend.status == "non_authoritative"
    assert any("backend identity" in reason for reason in missing_backend.reasons)
    assert fallback.status == "non_authoritative"
    assert any("fallback" in reason for reason in fallback.reasons)


def test_capability_assessment_marks_failed_release_profile() -> None:
    rows = []
    for coordinate in iter_run_coordinates():
        rows.append(
            {
                "run_key": coordinate.run_key,
                "benchmark_id": coordinate.benchmark_id,
                "family": coordinate.family,
                "model_style": coordinate.model_style,
                "solve_route": coordinate.solve_route,
                "strategy": coordinate.strategy,
                "platform": _platform_coordinate(),
                "status": "feasible",
                "feasible": True,
                "verification_status": "passed",
                "verification_passed": True,
            }
        )
    failed_ga = [dict(row) for row in rows]
    for row in failed_ga:
        if row["family"] == "interval_job_shop" and row["strategy"] == "ga":
            row["status"] = "verification_failed"
            row["feasible"] = False
            row["verification_status"] = "failed"
            row["verification_passed"] = False

    assessment = assess_capabilities(failed_ga)

    assert assessment["release_status"] == "failed"
    assert assessment["families"]["interval_job_shop"]["status"] == "experimental"
    assert (
        assessment["profiles"][
            "interval_job_shop|interval_var_sequence_no_overlap_precedence|native_search|ga|" + _platform_coordinate()
        ]["status"]
        == "failed"
    )


def test_release_gate_coordinates_and_lifecycle_are_explicit() -> None:
    coordinates = iter_run_coordinates()

    assert len(coordinates) == 22
    assert {coordinate.solve_route for coordinate in coordinates} == {"embedded_highs", "native_search"}
    assert all("|route=" in coordinate.run_key for coordinate in coordinates)
    assert case_lifecycle("jsplib_ft06") == "release_gate"
    assert case_lifecycle("jsplib_ft10") == "verified"
    assert len(case_lifecycle_inventory()) > len(RELEASE_GATE_PLAN)
    with pytest.raises(KeyError, match="unknown_case"):
        case_lifecycle("unknown_case")


def test_release_gate_strategy_configs_match_current_public_api() -> None:
    from dataclasses import fields

    from optagent import GaConfig

    budget = LocalRunBudget(max_iterations=1, time_limit_s=0.1, population_size=4, thread_count=1)
    expected_ga_fields = {
        "max_iterations",
        "unimproved_iteration_limit",
        "population_size",
        "crossover_rate",
    }

    for entry in RELEASE_GATE_PLAN:
        case = case_object_by_id(entry.benchmark_id)
        for strategy in entry.strategies:
            config = build_strategy_config(case=case, strategy_name=strategy, budget=budget)
            assert config is not None
            if isinstance(config, GaConfig):
                assert {field.name for field in fields(config)} == expected_ga_fields
                assert config.max_iterations is None
                assert config.population_size == 4
                assert config.crossover_rate == 0.35


def test_strategy_config_rejects_nonpositive_time_limit() -> None:
    case = case_object_by_id("jsplib_ft06")
    budget = LocalRunBudget(max_iterations=1, time_limit_s=0.0, population_size=4, thread_count=1)

    with pytest.raises(ValueError, match="time_limit_s must be > 0"):
        build_strategy_config(case=case, strategy_name="ga", budget=budget)


@pytest.mark.parametrize("strategy_name", ["alns", "lns"])
def test_strategy_config_marks_alns_unavailable_for_this_release(strategy_name: str) -> None:
    case = case_object_by_id("jsplib_ft06")
    budget = LocalRunBudget(max_iterations=1, time_limit_s=0.1, population_size=4, thread_count=1)

    with pytest.raises(ValueError, match="ALNS is temporarily unavailable"):
        build_strategy_config(case=case, strategy_name=strategy_name, budget=budget)


def test_authoritative_child_command_is_isolated_and_pins_the_model_style() -> None:
    planned = PlannedRun(
        benchmark_id="tsplib_berlin52",
        family="sequence_blackbox_tsp",
        tier="smoke",
        model_style="sequence_var_sequence_transition_sum",
        solve_route="native_search",
        strategy="ga",
        seed=11,
        max_iterations=5,
        time_limit_s=2.0,
        population_size=8,
        trace_limit=4,
        thread_count=1,
    )

    command = build_run_command("/tmp/python", planned, allow_download=False)

    assert command[0] == "/tmp/python"
    assert command[1].endswith("/benchmark.py")
    assert command[2:4] == ["run", "--case"]
    assert command[command.index("--model-style") + 1] == "sequence_var_sequence_transition_sum"
    assert command[command.index("--strategy") + 1] == "ga"
    assert command[-1] == "--no-download"


def test_authoritative_child_command_omits_unbounded_iteration_limit() -> None:
    planned = PlannedRun(
        benchmark_id="tsplib_berlin52",
        family="sequence_blackbox_tsp",
        tier="smoke",
        model_style="sequence_var_sequence_transition_sum",
        solve_route="native_search",
        strategy="ga",
        seed=11,
        max_iterations=None,
        time_limit_s=2.0,
        population_size=8,
        trace_limit=4,
        thread_count=1,
    )

    command = build_run_command("/tmp/python", planned, allow_download=True)

    assert "--max-iterations" not in command
    assert command[command.index("--time-limit-s") + 1] == "2.0"


def test_memory_hard_limit_is_only_enabled_on_linux() -> None:
    import sys

    limiter = _memory_limiter(4096)

    assert (limiter is not None) is sys.platform.startswith("linux")


def test_wheel_environment_does_not_inherit_system_packages(monkeypatch, tmp_path) -> None:
    calls = []
    monkeypatch.setattr(
        "benchmarks.authoritative_baseline.subprocess.run", lambda command, **kwargs: calls.append((command, kwargs))
    )

    _install_wheel_environment(
        bootstrap_python="/tmp/bootstrap-python",
        wheel_path=tmp_path / "optagent.whl",
        environment_dir=tmp_path / "venv",
    )

    assert calls[0][0] == ["/tmp/bootstrap-python", "-m", "venv", str(tmp_path / "venv")]
    assert "--system-site-packages" not in calls[0][0]
    assert calls[1][1]["capture_output"] is True
    assert calls[1][1]["text"] is True


def test_release_gate_checksums_cover_instance_and_reference_evidence() -> None:
    checksums = _data_checksums()

    for entry in RELEASE_GATE_PLAN:
        assert f"{entry.benchmark_id}:reference" in checksums
        if any(key.startswith(f"{entry.benchmark_id}:instance:") for key in checksums):
            continue
        case = case_object_by_id(entry.benchmark_id)
        assert case.data.get("instance_archive_url"), f"{entry.benchmark_id} has no governed local or downloadable data"


def test_backend_identity_uses_version_reported_by_installed_wheel() -> None:
    optx_run = next(run for run in planned_runs() if run.solve_route == "embedded_highs")

    identity = _backend_identity(
        optx_run,
        {"version": "1.2.0rc1", "embedded_highs_version": "9.9.9"},
    )

    assert identity == {"backend_name": "highs", "backend_version": "9.9.9"}


def test_authority_plan_only_validates_the_frozen_matrix(tmp_path, capsys) -> None:
    wheel = tmp_path / "optagent.whl"
    wheel.write_bytes(b"smoke-wheel")

    result = authority_main(
        [
            "--output-dir",
            str(tmp_path / "unused"),
            "--wheel",
            str(wheel),
            "--optagent-commit",
            "a" * 40,
            "--plan-only",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert result == 0
    assert payload["authoritative"] is False
    assert payload["planned_run_count"] == len(planned_runs())
