from __future__ import annotations

from benchmarks.authority import (
    HEURISTIC_SEEDS,
    RELEASE_GATE_PLAN,
    AuthorityInputs,
    assess_authority,
    assess_capabilities,
    expected_run_keys,
)
from benchmarks.run import LocalRunBudget, build_strategy_config, case_object_by_id
from benchmarks.authoritative_baseline import PlannedRun, _memory_limiter, build_run_command


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
            "run_key": run_key,
            "status": "feasible",
            "feasible": True,
            "verification_status": "passed",
            "verification_passed": True,
        }
        for run_key in sorted(expected_run_keys())
    ]
    accepted = assess_authority(
        AuthorityInputs(
            optagent_commit="a" * 40,
            benchmarks_commit="b" * 40,
            wheel_sha256="sha256:" + "c" * 64,
            optagent_dirty=False,
            benchmarks_dirty=False,
        ),
        rows,
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
    )
    incomplete = assess_authority(accepted.inputs, rows[:-1])
    unverified_rows = [dict(row) for row in rows]
    unverified_rows[0]["verification_passed"] = False
    unverified_rows[0]["verification_status"] = "not_run"
    unverified = assess_authority(accepted.inputs, unverified_rows)

    assert accepted.status == "authoritative"
    assert accepted.reasons == ()
    assert dirty.status == "non_authoritative"
    assert "optagent checkout is dirty" in dirty.reasons
    assert incomplete.status == "non_authoritative"
    assert any(reason.startswith("missing planned runs:") for reason in incomplete.reasons)
    assert unverified.status == "non_authoritative"
    assert any("independent verification" in reason for reason in unverified.reasons)


def test_capability_assessment_keeps_strategy_failures_separate_from_family_support() -> None:
    rows = []
    for entry in RELEASE_GATE_PLAN:
        for model_style in entry.model_styles:
            for strategy in entry.strategies:
                for seed in entry.seeds:
                    rows.append(
                        {
                            "run_key": f"{entry.benchmark_id}|{model_style}|{strategy}|seed={seed}|threads=1",
                            "benchmark_id": entry.benchmark_id,
                            "family": entry.family,
                            "model_style": model_style,
                            "strategy": strategy,
                            "status": "feasible",
                            "feasible": True,
                            "verification_status": "passed",
                            "verification_passed": True,
                        }
                    )
    failed_alns = [dict(row) for row in rows]
    for row in failed_alns:
        if row["family"] == "interval_job_shop" and row["strategy"] == "alns":
            row["status"] = "verification_failed"
            row["feasible"] = False
            row["verification_status"] = "failed"
            row["verification_passed"] = False

    assessment = assess_capabilities(failed_alns)

    assert assessment["release_status"] == "passed"
    assert assessment["families"]["interval_job_shop"]["status"] == "supported"
    assert (
        assessment["profiles"]["interval_job_shop|interval_var_sequence_no_overlap_precedence|alns"]["status"]
        == "failed"
    )


def test_release_gate_strategy_configs_match_current_public_api() -> None:
    budget = LocalRunBudget(max_iterations=1, time_limit_s=0.1, population_size=4, thread_count=1)

    for entry in RELEASE_GATE_PLAN:
        case = case_object_by_id(entry.benchmark_id)
        for strategy in entry.strategies:
            config = build_strategy_config(case=case, strategy_name=strategy, budget=budget)
            assert config is not None


def test_authoritative_child_command_is_isolated_and_pins_the_model_style() -> None:
    planned = PlannedRun(
        benchmark_id="tsplib_berlin52",
        family="sequence_blackbox_tsp",
        tier="smoke",
        model_style="sequence_var_sequence_transition_sum",
        strategy="ga",
        seed=11,
        max_iterations=5,
        time_limit_s=2.0,
        population_size=8,
        trace_limit=4,
        thread_count=1,
    )

    command = build_run_command("/tmp/python", planned, allow_download=False)

    assert command[:4] == ["/tmp/python", "-m", "benchmarks.run", "--case"]
    assert command[command.index("--model-style") + 1] == "sequence_var_sequence_transition_sum"
    assert command[command.index("--strategy") + 1] == "ga"
    assert command[-1] == "--no-download"


def test_memory_hard_limit_is_only_enabled_on_linux() -> None:
    import sys

    limiter = _memory_limiter(4096)

    assert (limiter is not None) is sys.platform.startswith("linux")
