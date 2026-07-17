# OptAgent Telemetry Metrics Dashboard

- Schema: `1`
- Runs: 798
- Strategies: 1
- Curve points: 5362

## Availability

| State | Count |
| --- | ---: |
| `available` | 6966 |
| `insufficient_data` | 3 |
| `null` | 17 |
| `unsupported` | 17 |

## Metric Sections

### effectiveness

| Metric | Availability | Value | Unit | Samples | Required | Actual |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| `effectiveness.by_strategy.ga.run_count` | `available` | 798 | runs |  |  |  |
| `effectiveness.by_strategy.ga.feasible_runs` | `available` | 778 | runs |  |  |  |
| `effectiveness.by_strategy.ga.solved_ratio` | `available` | 0.974937 | ratio |  |  |  |
| `effectiveness.by_strategy.ga.best_objective` | `available` | 3 |  | 798 |  |  |
| `effectiveness.by_strategy.ga.mean_objective` | `available` | 1.83847e+07 |  | 798 |  |  |
| `effectiveness.by_strategy.ga.mean_gap_to_reference` | `available` | 0.632424 |  | 798 |  |  |
| `effectiveness.by_strategy.ga.median_gap_to_reference` | `available` | 0.167886 |  | 798 |  |  |
| `effectiveness.by_strategy.ga.best_gap_to_reference` | `available` | 0 |  | 798 |  |  |

### efficiency

| Metric | Availability | Value | Unit | Samples | Required | Actual |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| `efficiency.by_strategy.ga.mean_wall_time_s` | `available` | 7.41127 | s | 798 |  |  |
| `efficiency.by_strategy.ga.mean_evaluated_candidates` | `available` | 23423.1 |  | 798 |  |  |
| `efficiency.by_strategy.ga.candidate_throughput_per_s` | `available` | 8793.69 | candidates/s | 798 |  |  |

### robustness

| Metric | Availability | Value | Unit | Samples | Required | Actual |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| `robustness.by_strategy.ga.run_count` | `available` | 798 | runs |  |  |  |
| `robustness.by_strategy.ga.success_rate` | `available` | 0.974937 | ratio |  |  |  |
| `robustness.by_strategy.ga.objective_mean` | `available` | 1.83847e+07 |  | 798 |  |  |
| `robustness.by_strategy.ga.objective_median` | `available` | 3872 |  | 798 |  |  |
| `robustness.by_strategy.ga.objective_stddev` | `available` | 1.2195e+08 |  | 778 |  |  |
| `robustness.by_strategy.ga.objective_variance` | `available` | 1.48718e+16 |  | 778 |  |  |
| `robustness.by_strategy.ga.objective_cv` | `available` | 6.63323 | ratio | 778 |  |  |
| `robustness.by_strategy.ga.objective_mean_ci95` | `available` | `complex` |  | 778 |  |  |
| `robustness.by_strategy.ga.gap_mean` | `available` | 0.632424 |  | 798 |  |  |
| `robustness.by_strategy.ga.gap_median` | `available` | 0.167886 |  | 798 |  |  |
| `robustness.by_strategy.ga.gap_stddev` | `available` | 2.24292 |  | 778 |  |  |
| `robustness.by_strategy.ga.gap_cv` | `available` | 3.54655 | ratio | 778 |  |  |
| `robustness.by_strategy.ga.gap_mean_ci95` | `available` | `complex` |  | 778 |  |  |

### anytime

| Metric | Availability | Value | Unit | Samples | Required | Actual |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| `anytime.by_strategy.ga.mean_primal_integral` | `available` | 13.3994 |  | 798 |  |  |
| `anytime.by_strategy.ga.mean_normalized_primal_integral` | `available` | 1.29477 | gap | 798 |  |  |
| `anytime.by_strategy.ga.mean_time_to_target_s` | `available` | 6.86938 | s | 798 |  |  |
| `anytime.by_strategy.ga.ecdf_target_hit_ratio` | `available` | 0.119048 | ratio |  |  |  |

### statistical_validity

| Metric | Availability | Value | Unit | Samples | Required | Actual |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| `statistical_validity.omnibus` | `insufficient_data` |  |  |  |  |  |
