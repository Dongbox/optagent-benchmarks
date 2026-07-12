# MIPLIB 2017

This source contains selected linear mixed-integer programs from the MIPLIB
2017 benchmark collection. It is the exact MIP capability track, not a primary
heuristic-search family.

Cases load governed MPS evidence, preserve variable integrality and linear
constraints, and minimize or maximize the declared linear objective. References
record an optimum or governed best-known bound with source provenance.

Large raw archives may be downloaded locally under `linear_mip/raw/`; only
release-gate evidence approved for offline redistribution should be committed.

Use `benchmarks.run --list-cases` for current IDs, lifecycle states, dimensions,
and references. Exact results always retain concrete backend name and version.
