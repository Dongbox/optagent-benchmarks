# OptAgent Telemetry Metrics Dashboard

- Schema: `1`
- Runs: 18
- Strategies: 1
- Curve points: 144

## Availability

| State | Count |
| --- | ---: |
| `available` | 222 |
| `insufficient_data` | 3 |

## Metric Sections

### effectiveness

| Metric | Availability | Value | Unit | Samples | Required | Actual |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| `effectiveness.by_strategy.ga.run_count` | `available` | 18 | runs |  |  |  |
| `effectiveness.by_strategy.ga.feasible_runs` | `available` | 18 | runs |  |  |  |
| `effectiveness.by_strategy.ga.solved_ratio` | `available` | 1 | ratio |  |  |  |
| `effectiveness.by_strategy.ga.best_objective` | `available` | 5.44923e+06 |  | 18 |  |  |
| `effectiveness.by_strategy.ga.mean_objective` | `available` | 914821 |  | 18 |  |  |
| `effectiveness.by_strategy.ga.mean_gap_to_reference` | `available` | 0.312799 |  | 18 |  |  |
| `effectiveness.by_strategy.ga.median_gap_to_reference` | `available` | 0.148995 |  | 18 |  |  |
| `effectiveness.by_strategy.ga.best_gap_to_reference` | `available` | 0.00415651 |  | 18 |  |  |

### efficiency

| Metric | Availability | Value | Unit | Samples | Required | Actual |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| `efficiency.by_strategy.ga.mean_wall_time_s` | `available` | 20.0119 | s | 18 |  |  |
| `efficiency.by_strategy.ga.mean_evaluated_candidates` | `available` | 217449 |  | 18 |  |  |
| `efficiency.by_strategy.ga.candidate_throughput_per_s` | `available` | 10866.6 | candidates/s | 18 |  |  |

### robustness

| Metric | Availability | Value | Unit | Samples | Required | Actual |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| `robustness.by_strategy.ga.run_count` | `available` | 18 | runs |  |  |  |
| `robustness.by_strategy.ga.success_rate` | `available` | 1 | ratio |  |  |  |
| `robustness.by_strategy.ga.objective_mean` | `available` | 914821 |  | 18 |  |  |
| `robustness.by_strategy.ga.objective_median` | `available` | 3873.5 |  | 18 |  |  |
| `robustness.by_strategy.ga.objective_stddev` | `available` | 2.09665e+06 |  | 18 |  |  |
| `robustness.by_strategy.ga.objective_variance` | `available` | 4.39593e+12 |  | 18 |  |  |
| `robustness.by_strategy.ga.objective_cv` | `available` | 2.29186 | ratio | 18 |  |  |
| `robustness.by_strategy.ga.objective_mean_ci95` | `available` | `complex` |  | 18 |  |  |
| `robustness.by_strategy.ga.gap_mean` | `available` | 0.312799 |  | 18 |  |  |
| `robustness.by_strategy.ga.gap_median` | `available` | 0.148995 |  | 18 |  |  |
| `robustness.by_strategy.ga.gap_stddev` | `available` | 0.406295 |  | 18 |  |  |
| `robustness.by_strategy.ga.gap_cv` | `available` | 1.2989 | ratio | 18 |  |  |
| `robustness.by_strategy.ga.gap_mean_ci95` | `available` | `complex` |  | 18 |  |  |

### anytime

| Metric | Availability | Value | Unit | Samples | Required | Actual |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| `anytime.by_strategy.ga.mean_primal_integral` | `available` | 16.5988 |  | 18 |  |  |
| `anytime.by_strategy.ga.mean_normalized_primal_integral` | `available` | 0.829939 | gap | 18 |  |  |
| `anytime.by_strategy.ga.mean_time_to_target_s` | `available` | 20 | s | 18 |  |  |
| `anytime.by_strategy.ga.ecdf_target_hit_ratio` | `available` | 0 | ratio |  |  |  |

### statistical_validity

| Metric | Availability | Value | Unit | Samples | Required | Actual |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| `statistical_validity.omnibus` | `insufficient_data` |  |  |  |  |  |
