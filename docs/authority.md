# Authority And Capability

## Purpose

Benchmark results support a scoped claim:

> For explicitly supported problem families, model styles, and solve routes,
> the supplied OptAgent wheel produces independently verified feasible
> solutions under a fixed budget and environment, with quality measured against
> governed references.

The suite does not claim universal optimization capability.

## Capability Classification

- **Built-in native capability** requires no solver-specific installation beyond
  the base OptAgent wheel. GA, ALNS, and the embedded HiGHS-backed OptX route
  are currently classified this way.
- **OptAgent-authored search capability** is the subset implemented by OptAgent
  search code, currently GA and ALNS.
- **Extra capability** requires an optional dependency. OR-Tools CP-SAT and
  MathOpt routes are reported separately.
- Every result retains its concrete backend name and version.

The full capability coordinate is:

```text
problem family x model style x solve route x strategy x platform
```

A family does not imply support for modeling primitives that its cases do not
exercise.

## Release Gate

The executable matrix is `benchmarks.authority.RELEASE_GATE_PLAN`. It covers six
heuristic families and a separate embedded-HiGHS exact track. Distinct model
styles, including TSP External Function and DAG IR transition-sum models, remain
separate evidence.

- Heuristic release-gate runs use seeds `11`, `23`, and `47`.
- Deterministic exact routes run once.
- Explicit strategy runs may not silently fall back.
- Every returned solution is checked by a benchmark-owned verifier.
- Every run uses a separate process with an external hard timeout and a memory
  limit where supported.
- Linux x86_64 is the authoritative performance platform. macOS arm64 and
  Windows x86_64 are correctness and packaging gates; their timings are not
  pooled with Linux.

## Authority Requirements

An artifact is `authoritative` only when:

- the benchmark checkout was clean before execution;
- the full benchmark commit SHA is recorded;
- the supplied OptAgent commit identity, wheel SHA256, and installed version
  are recorded;
- every planned coordinate exists exactly once;
- every returned solution was independently verified;
- raw instance and reference evidence used by the release gate is checksummed;
- explicit-strategy fallback remains zero.

The benchmark maintainer does not need OptAgent repository access. A trusted
wheel plus its declared source commit identity is sufficient. If the wheel
provenance cannot be established, the run remains useful evidence but is marked
`non_authoritative`.

Authority and capability are separate. An authoritative artifact can truthfully
show a crash, timeout, invalid solution, or unsupported profile.

## Case Lifecycle

Cases use governed lifecycle states:

- `declared`: metadata exists;
- `runnable`: data, parser, model builder, and local smoke work;
- `verified`: independent verifier and governed reference are available;
- `release_gate`: representative case in the executable release matrix;
- `experimental`: runnable, but not accepted as supported capability evidence;
- `retired`: retained for historical evidence only.

Registry membership alone is not capability evidence.

## Execution Tiers

- `smoke`: representative cases for every change;
- `release-gate`: clean wheel, frozen matrix, authoritative artifact;
- `extended`: broader inventory, normally scheduled;
- `pressure`: scale, timeout, memory, and incumbent-preservation behavior.

Pressure cases may miss ordinary quality targets, but must not crash or return
an invalid solution.

## Metrics And Fairness

- Reliability and independent feasibility are hard gates.
- Typical quality uses median reference gap; stability uses p90 or worst-case
  gap. Best seed is display-only.
- End-to-end API time is the public efficiency metric. Lowering, callback,
  solver, and decode time are diagnostic breakdowns.
- Incumbent traces must be complete and monotonic before anytime metrics are
  authoritative.
- Official configurations are frozen by family, model style, and tier.
- Per-case tuning and benchmark-ID special cases are prohibited.
- Calibration cases and release holdouts are disjoint.
- External comparisons use the same hardware, budget, and timing boundary.

## Run An Authoritative Baseline

From the `benchmarks/` repository directory:

```bash
PYTHONPATH=.. ./.venv/bin/python -m benchmarks.authoritative_baseline \
  --output-dir /artifact-storage/authoritative-baseline \
  --wheel /path/to/optagent.whl \
  --python-executable ./.venv/bin/python \
  --allow-download \
  --require-authoritative
```

The output directory must be empty. The command installs the wheel into an
isolated child environment and writes immutable `manifest.json` and
`rows.jsonl` evidence.

Authority evidence answers whether a wheel demonstrates a capability. GA
before/after performance is a separate paired experiment described in
[GA strategy comparison](ga-comparison.md).
