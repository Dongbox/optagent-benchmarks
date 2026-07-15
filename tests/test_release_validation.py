from __future__ import annotations

from collections import Counter

from benchmarks.release_validation import (
    RELEASE_VALIDATION_SEEDS,
    REPEAT_SEEDS,
    REPRESENTATIVE_CASE_IDS,
    build_release_plan,
)


def test_release_plan_covers_every_implemented_family_twice() -> None:
    plan = build_release_plan()
    representative = plan["representative_cases"]
    family_counts = Counter(row["family"] for row in representative)

    assert len(representative) == len(REPRESENTATIVE_CASE_IDS) == 14
    assert set(family_counts.values()) == {2}
    assert set(family_counts) == {
        "cumulative_resource_scheduling",
        "exact_linear_mip",
        "flexible_interval_job_shop",
        "interval_job_shop",
        "sequence_blackbox_tsp",
        "sequence_quadratic_assignment",
        "sequence_transition_penalty",
    }


def test_release_plan_uses_ten_seeds_and_three_same_seed_repetitions() -> None:
    plan = build_release_plan()

    for row in plan["representative_cases"]:
        if row["family"] == "exact_linear_mip":
            assert row["seeds"] == [0]
            assert row["repeat_seeds"] == []
            assert row["repeat_count"] == 1
        else:
            assert row["seeds"] == list(RELEASE_VALIDATION_SEEDS)
            assert row["repeat_seeds"] == list(REPEAT_SEEDS)
            assert row["repeat_count"] == 3
    assert len(RELEASE_VALIDATION_SEEDS) == 10
    assert len(REPEAT_SEEDS) == 3


def test_linux_full_plan_contains_the_registered_inventory() -> None:
    plan = build_release_plan()

    assert len(plan["linux_full"]["case_ids"]) == 196
    assert len(plan["linux_full"]["cases"]) == 196
    assert plan["linux_full"]["seed"] == 11
