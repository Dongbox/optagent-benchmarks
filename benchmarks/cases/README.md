# Benchmark Cases

`benchmarks/cases/` owns benchmark declarations, source loaders, governed references,
model builders, solution decoding, and independent verification.

## Source Collections

- [TSPLIB](tsplib/README.md): symmetric TSP and sequence-model variants
- [QAPLIB](qaplib/README.md): quadratic assignment
- [JSPLIB](jsplib/README.md): job-shop scheduling
- [FJSPLIB](fjsplib/README.md): flexible job-shop scheduling
- [PSPLIB](psplib/README.md): resource-constrained project scheduling
- [MIPLIB 2017](miplib2017/README.md): exact linear MIP track
- [Custom](custom/README.md): benchmark-owned domain cases

## Inventory

Do not maintain a complete case list in Markdown. Query the registry:

```bash
./.venv/bin/python benchmark.py list-cases
```

The registry owns IDs, families, tiers, model styles, lifecycle state, size,
references, and data paths. Source README files describe stable source and
format semantics only.

## Layout

```text
benchmarks/cases/<source>/<problem>/
    __init__.py       source aggregation
    _domain.py        shared parsing/model/verification logic when needed
    <case>.py         declarations
    raw/              governed source files or local download cache
```

Public sources and custom cases use the same `BenchmarkCase` contract. Raw
caches are not documentation and should be committed only when licensing and
offline release-gate requirements permit it.

## Maintenance Rules

- IDs are lowercase and source-prefixed, for example `tsplib_berlin52`.
- A reference states its provenance and whether it is an optimum, bound, or
  best-known value.
- Independent verification must not trust solver-reported feasibility or
  objective fields.
- Case-specific tuning and benchmark-ID strategy special cases are prohibited.
- New release-gate cases require stable local data and evidence checksums.
- Registry discovery flows through `cases/registry.py`; runners do not import
  every case module manually.
