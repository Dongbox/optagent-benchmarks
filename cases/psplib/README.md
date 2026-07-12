# PSPLIB

This source contains selected PSPLIB J90 resource-constrained project
scheduling instances.

Each activity has a duration, renewable-resource demands, and precedence arcs.
The model enforces precedence and cumulative capacity constraints and minimizes
project makespan.

Independent verification checks activity timing, all precedence arcs,
time-indexed renewable-resource capacity, and recomputed makespan.

Use `benchmarks.run --list-cases` for current IDs, tiers, sizes, and references.
Raw `.rcp` files belong under `rcpsp/raw/`; downloaded files are local caches
unless explicitly governed as release evidence.
