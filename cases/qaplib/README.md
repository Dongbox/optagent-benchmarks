# QAPLIB

This source contains quadratic assignment instances from
[QAPLIB](https://qaplib.mgi.polymtl.ca). A public archive is also available via
[DOI 10.7488/ds/3428](https://doi.org/10.7488/ds/3428).

## Matrix Semantics

QAPLIB `.dat` files provide two `n x n` matrices in source order. The loader
preserves that order and evaluates:

```text
sum A[i][j] * B[p[i]][p[j]]
```

Names such as `flow` and `distance` are conventional and may not describe every
instance. Swapping the matrices defines an equivalent optimization problem but
does not preserve the cost of the same permutation.

`.sln` files and governed solution tables provide reference provenance.
Independent verification checks that the assignment is a permutation and
recomputes the quadratic objective.

Use `benchmarks.run --list-cases` for current IDs, tiers, sizes, structural
metadata, and references. Full archives may be cached below
`quadratic_assignment/raw/`; selected offline cases live at the loader's
governed paths.
