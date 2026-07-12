# QAPLIB

二次指派实例来自 [QAPLIB](https://qaplib.mgi.polymtl.ca)，公共归档也可通过
[DOI 10.7488/ds/3428](https://doi.org/10.7488/ds/3428) 获取。

## 矩阵语义

QAPLIB `.dat` 按源文件顺序提供两个 `n x n` 矩阵。Loader 保持该顺序并计算：

```text
sum A[i][j] * B[p[i]][p[j]]
```

`flow`、`distance` 等名称是惯例，不一定准确描述所有实例。交换两个矩阵会形成等价优化
问题，但不会保持同一 permutation 的 cost。

`.sln` 和受治理 solution table 提供 reference 来源。独立验证检查 assignment 是
permutation，并重新计算二次目标。

```bash
./.venv/bin/python benchmark.py list-cases --family sequence_quadratic_assignment
```
