# GA Strategy Comparison

## Purpose

The paired comparison decides whether a challenger GA wheel improves on an
approved baseline wheel under an identical frozen protocol. The matched
coordinate is:

```text
family x model style x case x seed x budget x platform
```

The benchmark **Delta Index** is a baseline-relative experimental index. It is
not the Native Kernel search-candidate `Score` and is meaningful only within one
protocol and index-profile version.

## Protocols

- `ga_release_smoke_v1`: one case per profile and three seeds. Detects hard
  failures and obvious regressions. It cannot return a promotable improvement.
- `ga_calibration_v1`: three calibration cases per profile and ten seeds. The
  steel profile has limited generalization because fewer cases exist.
- `ga_release_holdout_v1`: two holdout cases per profile and ten seeds. Run only
  after configuration and implementation choices are frozen.

Each protocol freezes cases, seeds, wall time, search-candidate checkpoint,
population size, maximum iterations, trace limit, thread count, execution
order, performance platform, and index profile. Changing any frozen field
requires a new protocol ID.

## Validity Gates

Validity is lexicographic and cannot be compensated by quality:

- independent verification passes for baseline and challenger;
- errors and timeouts do not increase;
- explicit strategy fallback is zero;
- the requested matrix is complete;
- incumbent and candidate-checkpoint evidence is complete;
- incumbent quality is monotonic;
- protocol, index profile, cases, evidence checksums, seeds, budgets, platform,
  and thread count match;
- implementation comparisons use identical strategy configuration;
- configuration comparisons use the same wheel and OptAgent commit.

Missing or malformed trace-overflow evidence makes the run invalid.
Incompatible artifacts receive no Delta Index. Invalid artifacts are retained
for diagnosis but cannot be promoted.

## Delta Index

The approved profile is `ga_strategy_comparison_index_v1`:

```text
Overall Delta Index =
  40% Quality
  30% Anytime
  20% Robustness
  10% Efficiency
```

| Dimension | Components |
| --- | --- |
| Quality | 70% median final reference gap, 30% paired win rate |
| Anytime | 60% normalized primal integral, 25% target hit rate, 15% time-to-target |
| Robustness | 50% p90 final gap, 30% gap MAD, 20% cross-case direction consistency |
| Efficiency | 50% search-candidate throughput, 50% elapsed time at the fixed candidate checkpoint |

Components map to `[-100, 100]` using predeclared meaningful-change thresholds.
Baseline is zero. Positive values improve on baseline; negative values regress.
Families are equally weighted. Worst gap is a separate regression guard.

The fixed candidate-checkpoint metric accepts only dedicated canonical
`candidate_checkpoint` events with cumulative evaluated-candidate counts. It is
unavailable rather than estimated from termination time when the checkpoint is
not observed.

## Statistical Evidence

The primary uncertainty estimate is a deterministic hierarchical bootstrap:
cases are resampled first, then seeds within cases. The global interval averages
profile medians within each family and then weights families equally.

Reports also contain paired win/tie/loss counts, Wilcoxon signed-rank results
when enough pairs exist, and profile-keyed Holm correction.

Verdicts are `improved`, `neutral`, `mixed`, `regressed`, `invalid`, and
`incompatible`. Promotion requires `improved`, a positive confidence interval,
no invalid or regressed profile, no dimension below the regression guard, and
all hard gates passing.

## Run A Pair

Only the two wheel files are required. OptAgent source access is not required.

```bash
./.venv/bin/python benchmark.py compare-ga run-pair \
  --protocol ga_release_smoke_v1 \
  --baseline-wheel /path/to/baseline.whl \
  --challenger-wheel /path/to/challenger.whl \
  --baseline-commit <baseline-source-sha> \
  --challenger-commit <challenger-source-sha> \
  --output-dir /artifact-storage/ga-smoke
```

Add `--allow-download` only when governed case data is not already cached. The
runner installs each wheel in a separate temporary environment and alternates
execution order within pairs.

Formal efficiency comparison is authoritative only on Linux x86_64. Smoke
correctness can run on other supported platforms.

## Compare Existing Artifacts

```bash
./.venv/bin/python benchmark.py compare-ga compare \
  --baseline /artifact-storage/run/baseline \
  --challenger /artifact-storage/run/challenger \
  --output-dir /artifact-storage/recomparison
```

Comparison output:

```text
comparison_manifest.json
paired_rows.jsonl
dimension_metrics.json
statistical_evidence.json
delta_index.json
feedback.md
```

## Promote A Baseline

Promotion is explicit and immutable:

```bash
./.venv/bin/python benchmark.py compare-ga promote \
  --comparison-dir /artifact-storage/ga-holdout/comparison \
  --registry /artifact-storage/ga-baselines.json \
  --approved-by maintainer@example.com
```

Promotion reloads the complete challenger artifact, verifies every declared
checksum, and confirms that its manifest is the one used by the comparison.
The registry retains the previous baseline and complete promotion history.

Keep compact approved summaries and checksums in Git if required by governance.
Store full telemetry, curves, paired rows, logs, and machine samples in
immutable artifact storage.
