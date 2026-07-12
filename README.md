# OptAgent Benchmarks

`optagent-benchmarks` is the independently maintained benchmark repository for
OptAgent. Benchmark maintainers work from released or supplied OptAgent wheels;
access to the OptAgent source repository is not required.

This repository owns benchmark cases and verifiers, suite execution, capability
evidence, paired GA comparisons, and telemetry-derived evaluation artifacts. It
does not own OptAgent runtime semantics or solver implementation details.

## Documentation

- [Authority and capability](docs/authority.md)
- [GA strategy comparison](docs/ga-comparison.md)
- [Telemetry, metrics, and artifacts](docs/telemetry-artifacts.md)
- [Case sources and maintenance](benchmarks/cases/README.md)

## Setup

The checkout directory may have any name. Run all commands from its root:

```bash
git clone https://github.com/Dongbox/optagent-benchmarks.git optagent-benchmarks
cd optagent-benchmarks
python -m venv .venv
./.venv/bin/python -m pip install --upgrade pip pytest ruff
./.venv/bin/python -m pip install /path/to/optagent.whl
```

Use a clean environment for release evidence. Do not install an editable
OptAgent source checkout there. For explicit local source development only, set
`OPTAGENT_SOURCE_ROOT=/path/to/optagent`.

## Commands

List cases:

```bash
./.venv/bin/python benchmark.py list-cases
./.venv/bin/python benchmark.py list-cases --family sequence_blackbox_tsp --tier smoke
```

Run one diagnostic case:

```bash
./.venv/bin/python benchmark.py run \
  --case tsplib_berlin52 \
  --strategy ga \
  --model-style sequence_var_external_call \
  --no-download \
  --max-iterations 10 \
  --population-size 8 \
  --time-limit-s 0.5
```

Run an artifact-producing suite:

```bash
./.venv/bin/python benchmark.py suite \
  --family sequence_blackbox_tsp \
  --tier smoke \
  --strategy ga \
  --timestamp local-smoke
```

Compare baseline and challenger OptAgent wheels with the frozen GA protocol:

```bash
./.venv/bin/python benchmark.py compare-ga run-pair \
  --protocol ga_release_smoke_v1 \
  --baseline-wheel /path/to/baseline.whl \
  --challenger-wheel /path/to/challenger.whl \
  --baseline-commit <baseline-sha> \
  --challenger-commit <challenger-sha> \
  --output-dir /tmp/ga-smoke
```

Smoke detects invalid evidence and obvious regressions but cannot produce an
`improved` promotion verdict. Continue with `ga_calibration_v1` and then
`ga_release_holdout_v1`. See [GA strategy comparison](docs/ga-comparison.md).

Produce an authoritative release-gate baseline:

```bash
./.venv/bin/python benchmark.py authority \
  --output-dir /artifact-storage/authoritative-baseline \
  --wheel /path/to/optagent.whl \
  --optagent-commit <optagent-sha> \
  --allow-download \
  --require-authoritative
```

Publish telemetry artifacts and render their dashboard:

```bash
./.venv/bin/python benchmark.py publish-telemetry \
  /path/to/run-telemetry.json \
  --output-dir /tmp/telemetry-artifacts \
  --reference toy-001=10.0

./.venv/bin/python benchmark.py dashboard \
  /tmp/telemetry-artifacts \
  --output-root /tmp/telemetry-dashboard
```

Run `./.venv/bin/python benchmark.py --help` or append `--help` to any
subcommand for the complete interface.

## Development

```bash
./.venv/bin/python -m pytest -q
./.venv/bin/ruff check benchmark.py benchmarks tests
./.venv/bin/python -m compileall benchmark.py benchmarks tests
./.venv/bin/python benchmark.py list-cases --tier smoke
```

For case changes, also run one small `--no-download` case in the affected
family. Generated output and downloaded raw caches are not documentation and
must not be committed unless a case contract governs them as source evidence.

## Repository Layout

```text
benchmark.py       single command-line entrypoint
benchmarks/        implementation, cases, verifiers, and presentation code
docs/              benchmark-owned policies and data contracts
tests/             governance, artifact, metric, and case regression tests
```
