# Solution Metrics And Presentation Boundary

This document defines the boundary between benchmark cases, the local runner,
and presentation code.

## Responsibilities

- `cases/` declares benchmark metadata, builds OptAgent models, and decodes
  domain facts that only the case understands.
- `run.py` owns local execution, standard solver fields, gap calculation, and
  result-row assembly for lightweight runs.
- `presentation/` owns suite workspaces, reports, artifact dashboard rendering,
  display truncation, and formatting.
- `telemetry_metrics.py` owns five-dimensional metric derivation from canonical
  runtime telemetry.

## Case Interface

Current case implementations should expose narrow solution metrics:

```python
case.solution_metrics(solution, **build_kwargs) -> dict[str, Any]
```

Allowed fields:

- `objective`
- `raw_objective`
- `reference_objective`
- `decoded_solution`
- `model_style`
- small domain diagnostics needed for audit

Cases should not return:

- solver-common fields such as status, feasible, runtime, or solver name;
- derived row fields such as gap, strategy profile, or time-to-best;
- dashboard-only display fields such as `sequence_head` or
  `machine_order_head`;
- static labels that already exist in case metadata.

`solution_summary()` may remain only as a compatibility alias to
`solution_metrics()` while older cases are being narrowed.

## Presentation Rules

- Presentation may derive compact display fields from `decoded_solution`.
- Presentation must not read case-private build context or node ids.
- Runner and cases must not exchange benchmark-specific wrapper model types.
- Domain objective recomputation belongs in cases because it is correctness
  evidence, not display formatting.
- Telemetry-derived metrics must flow through `telemetry_metrics.py` and
  `telemetry_artifacts.py`, not through case-level display helpers.
