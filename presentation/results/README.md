# Historical Results

This directory contains legacy Git-managed benchmark summaries used by older
dashboard flows.

Do not add current telemetry metrics here and do not edit generated indexes or
aggregates by hand. New dashboard data flows through:

```text
canonical telemetry -> telemetry_artifacts -> immutable artifact -> dashboard
```

See [Telemetry, metrics, and artifacts](../../docs/telemetry-artifacts.md).
