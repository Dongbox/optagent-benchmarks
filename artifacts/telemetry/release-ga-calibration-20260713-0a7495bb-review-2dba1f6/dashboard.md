# OptAgent Telemetry Metrics Dashboard

- Schema: `1`
- Runs: 320
- Strategies: 1
- Curve points: 2116

## Availability

| State | Count |
| --- | ---: |
| `available` | 2798 |
| `insufficient_data` | 3 |

## Metric Sections

### effectiveness

| Metric | Availability | Value | Unit | Samples | Required | Actual |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| `effectiveness.by_strategy.ga.run_count` | `available` | 320 | runs |  |  |  |
| `effectiveness.by_strategy.ga.feasible_runs` | `available` | 320 | runs |  |  |  |
| `effectiveness.by_strategy.ga.solved_ratio` | `available` | 1 | ratio |  |  |  |
| `effectiveness.by_strategy.ga.best_objective` | `available` | 27076 |  | 320 |  |  |
| `effectiveness.by_strategy.ga.mean_objective` | `available` | 3.6622e+07 |  | 320 |  |  |
| `effectiveness.by_strategy.ga.mean_gap_to_reference` | `available` | 1.77902 |  | 320 |  |  |
| `effectiveness.by_strategy.ga.median_gap_to_reference` | `available` | 0.72058 |  | 320 |  |  |
| `effectiveness.by_strategy.ga.best_gap_to_reference` | `available` | 0 |  | 320 |  |  |

### efficiency

| Metric | Availability | Value | Unit | Samples | Required | Actual |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| `efficiency.by_strategy.ga.mean_wall_time_s` | `available` | 0.0330093 | s | 320 |  |  |
| `efficiency.by_strategy.ga.mean_evaluated_candidates` | `available` | 336 |  | 320 |  |  |
| `efficiency.by_strategy.ga.candidate_throughput_per_s` | `available` | 36968.3 | candidates/s | 320 |  |  |

### robustness

| Metric | Availability | Value | Unit | Samples | Required | Actual |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| `robustness.by_strategy.ga.run_count` | `available` | 320 | runs |  |  |  |
| `robustness.by_strategy.ga.success_rate` | `available` | 1 | ratio |  |  |  |
| `robustness.by_strategy.ga.objective_mean` | `available` | 3.6622e+07 |  | 320 |  |  |
| `robustness.by_strategy.ga.objective_median` | `available` | 75991 |  | 320 |  |  |
| `robustness.by_strategy.ga.objective_stddev` | `available` | 1.69063e+08 |  | 320 |  |  |
| `robustness.by_strategy.ga.objective_variance` | `available` | 2.85822e+16 |  | 320 |  |  |
| `robustness.by_strategy.ga.objective_cv` | `available` | 4.61643 | ratio | 320 |  |  |
| `robustness.by_strategy.ga.objective_mean_ci95` | `available` | `complex` |  | 320 |  |  |
| `robustness.by_strategy.ga.gap_mean` | `available` | 1.77902 |  | 320 |  |  |
| `robustness.by_strategy.ga.gap_median` | `available` | 0.72058 |  | 320 |  |  |
| `robustness.by_strategy.ga.gap_stddev` | `available` | 2.87432 |  | 320 |  |  |
| `robustness.by_strategy.ga.gap_cv` | `available` | 1.61568 | ratio | 320 |  |  |
| `robustness.by_strategy.ga.gap_mean_ci95` | `available` | `complex` |  | 320 |  |  |

### anytime

| Metric | Availability | Value | Unit | Samples | Required | Actual |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| `anytime.by_strategy.ga.mean_primal_integral` | `available` | 8.91307 |  | 320 |  |  |
| `anytime.by_strategy.ga.mean_normalized_primal_integral` | `available` | 1.78261 | gap | 320 |  |  |
| `anytime.by_strategy.ga.mean_time_to_target_s` | `available` | 4.84377 | s | 320 |  |  |
| `anytime.by_strategy.ga.ecdf_target_hit_ratio` | `available` | 0.03125 | ratio |  |  |  |

### statistical_validity

| Metric | Availability | Value | Unit | Samples | Required | Actual |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| `statistical_validity.omnibus` | `insufficient_data` |  |  |  |  |  |
