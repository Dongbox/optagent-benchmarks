# OptAgent Telemetry Metrics Dashboard

- Schema: `1`
- Runs: 20
- Strategies: 1
- Curve points: 80

## Availability

| State | Count |
| --- | ---: |
| `available` | 162 |
| `insufficient_data` | 3 |

## Metric Sections

### effectiveness

| Metric | Availability | Value | Unit | Samples | Required | Actual |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| `effectiveness.by_strategy.ga.run_count` | `available` | 20 | runs |  |  |  |
| `effectiveness.by_strategy.ga.feasible_runs` | `available` | 20 | runs |  |  |  |
| `effectiveness.by_strategy.ga.solved_ratio` | `available` | 1 | ratio |  |  |  |
| `effectiveness.by_strategy.ga.best_objective` | `available` | 1610 |  | 20 |  |  |
| `effectiveness.by_strategy.ga.mean_objective` | `available` | 14603.5 |  | 20 |  |  |
| `effectiveness.by_strategy.ga.mean_gap_to_reference` | `available` | 0.0447468 |  | 20 |  |  |
| `effectiveness.by_strategy.ga.median_gap_to_reference` | `available` | 0.0118015 |  | 20 |  |  |
| `effectiveness.by_strategy.ga.best_gap_to_reference` | `available` | 0 |  | 20 |  |  |

### efficiency

| Metric | Availability | Value | Unit | Samples | Required | Actual |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| `efficiency.by_strategy.ga.mean_wall_time_s` | `available` | 2.00909 | s | 20 |  |  |
| `efficiency.by_strategy.ga.mean_evaluated_candidates` | `available` | 12632.4 |  | 20 |  |  |
| `efficiency.by_strategy.ga.candidate_throughput_per_s` | `available` | 6280.1 | candidates/s | 20 |  |  |

### robustness

| Metric | Availability | Value | Unit | Samples | Required | Actual |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| `robustness.by_strategy.ga.run_count` | `available` | 20 | runs |  |  |  |
| `robustness.by_strategy.ga.success_rate` | `available` | 1 | ratio |  |  |  |
| `robustness.by_strategy.ga.objective_mean` | `available` | 14603.5 |  | 20 |  |  |
| `robustness.by_strategy.ga.objective_median` | `available` | 3015 |  | 20 |  |  |
| `robustness.by_strategy.ga.objective_stddev` | `available` | 29313.8 |  | 20 |  |  |
| `robustness.by_strategy.ga.objective_variance` | `available` | 8.59301e+08 |  | 20 |  |  |
| `robustness.by_strategy.ga.objective_cv` | `available` | 2.00732 | ratio | 20 |  |  |
| `robustness.by_strategy.ga.objective_mean_ci95` | `available` | `complex` |  | 20 |  |  |
| `robustness.by_strategy.ga.gap_mean` | `available` | 0.0447468 |  | 20 |  |  |
| `robustness.by_strategy.ga.gap_median` | `available` | 0.0118015 |  | 20 |  |  |
| `robustness.by_strategy.ga.gap_stddev` | `available` | 0.0585443 |  | 20 |  |  |
| `robustness.by_strategy.ga.gap_cv` | `available` | 1.30835 | ratio | 20 |  |  |
| `robustness.by_strategy.ga.gap_mean_ci95` | `available` | `complex` |  | 20 |  |  |

### anytime

| Metric | Availability | Value | Unit | Samples | Required | Actual |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| `anytime.by_strategy.ga.mean_primal_integral` | `available` | 0.128573 |  | 20 |  |  |
| `anytime.by_strategy.ga.mean_normalized_primal_integral` | `available` | 0.0642866 | gap | 20 |  |  |
| `anytime.by_strategy.ga.mean_time_to_target_s` | `available` | 1.16797 | s | 20 |  |  |
| `anytime.by_strategy.ga.ecdf_target_hit_ratio` | `available` | 0.45 | ratio |  |  |  |

### statistical_validity

| Metric | Availability | Value | Unit | Samples | Required | Actual |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| `statistical_validity.omnibus` | `insufficient_data` |  |  |  |  |  |
