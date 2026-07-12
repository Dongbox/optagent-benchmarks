# FJSPLIB

This source contains flexible job-shop scheduling instances collected from the
[SchedulingLab FJSP archive](https://github.com/SchedulingLab/fjsp-instances).

## Local Data

- Original `.txt` instances and normalized `.json` evidence live under
  `fjobshop/raw/`.
- Normalized JSON is the loader contract used by offline runs.
- A JSON instance records machine count, jobs, operations, candidate machines,
  processing times, and reference provenance.
- `reference.kind=optimum` denotes a closed optimum; `bounds` denotes governed
  lower/upper or best-known bounds.

## Model

Each operation has optional interval alternatives for eligible machines.
Presence variables and `exactly_one` select a machine. Selected start/end
projections define precedence. Per-machine sequence/no-overlap constraints
prevent overlap. The objective minimizes makespan.

Independent verification checks one selected alternative per operation,
operation precedence, machine non-overlap, and recomputed makespan.

Use `benchmarks.run --list-cases` for current IDs, tiers, sizes, series, and
references. Do not duplicate the registry inventory here.
