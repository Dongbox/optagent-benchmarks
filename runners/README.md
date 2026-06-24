# Benchmark Runners

`benchmarks.run` is the lightweight local entrypoint for listing cases and running one case directly.

Files in `benchmarks.runners` are not the default place for new generic execution logic. A runner file in this directory must correspond to a concrete evaluation scenario, such as:

- CI smoke suite;
- dashboard publication input generation;
- strategy comparison report;
- multi-seed calibration;
- ablation study;
- performance or parallel matrix benchmark.

Scenario runners may select cases, build strategy matrices, normalize rows, and write artifacts. They must not define public raw-data parsing, default case metadata, default problem descriptions, default model builders, or instance-family default strategy configuration. Those belong in `benchmarks.cases`.

Current scenario entrypoints:

- `run.py` / `suite.py`: standard artifact-writing benchmark suite scenario.
