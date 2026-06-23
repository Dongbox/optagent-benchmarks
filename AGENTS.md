# AGENTS.md

## Purpose

This repository contains the public OptAgent benchmark harness. It is also used
as the `benchmarks/` submodule of the private `optagent` repository.

The benchmark repository must remain runnable against an installed OptAgent
package through the public Python API. It must not depend on private source-tree
internals from the parent repository.

## Rules

- Treat `README.md`, `docs/result-json-contract.md`, and
  `docs/dashboard-data-contract.md` as the benchmark contract entrypoints.
- Keep benchmark models limited to public OptAgent modeling and solve APIs.
- Keep data loading in `loaders/`, public API model construction in `models/`,
  and execution / artifact writing in `runners/`.
- Keep `catalog/` and `definitions/` versioned and reviewable; they describe
  public benchmark cases and modeling declarations.
- Do not commit downloaded raw benchmark data, private datasets, credentials,
  local wheel files, virtual environments, Python caches, or local run logs.
- Do not make benchmark correctness depend on private OptAgent metadata or
  parent-repository-only files.
- Commit `results/` and `aggregates/` changes only when they are intentional,
  schema-compatible benchmark or dashboard artifacts with clear provenance.
- Preserve immutable published result artifacts unless a task explicitly calls
  for regenerating or replacing them.

## Validation

- For loader, model, runner, schema, or result-contract changes, run the focused
  pytest tests or a focused `python -m benchmarks.runners.run ...` smoke command.
- For broad benchmark harness changes, run `python -m benchmarks.runners.run --tier smoke`
  when the required OptAgent package and benchmark data access are available.
- If validation is skipped, record what was not validated and why.

## Submodule Use

When working from the parent `optagent` repository, keep the submodule branch
aligned with the parent branch when possible. Commit submodule changes in this
repository before updating the parent repository's submodule pointer.
