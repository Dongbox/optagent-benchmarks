# TSPLIB

This source contains symmetric traveling-salesperson instances from
[TSPLIB95](https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/). The local
reference table is derived from the published symmetric-TSP optimum list.

## Supported Distance Formats

- `EUC_2D`: rounded two-dimensional Euclidean distance
- `CEIL_2D`: ceiling Euclidean distance
- `ATT`: TSPLIB pseudo-Euclidean distance
- `GEO`: TSPLIB geographical distance
- `EXPLICIT`: `FULL_MATRIX`, row-triangular, and diagonal-triangular matrices

The loader implements TSPLIB rounding rules. Independent verification checks a
Hamiltonian permutation and recomputes the closed-tour length from governed
source data.

The same instance family may expose separate model styles, including External
Function tour cost and DAG IR transition-sum cost. They remain separate
capability and GA-comparison profiles.

Use `benchmarks.run --list-cases` for current IDs, tiers, node counts,
structural statistics, model styles, and references. Full archives may be
cached below `tsp/raw/`; selected offline cases live at governed loader paths.
