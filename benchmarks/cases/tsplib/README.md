# TSPLIB

对称旅行商实例来自
[TSPLIB95](https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/)，本地 reference table
来源于公开的 symmetric-TSP optimum list。

## 支持的距离格式

- `EUC_2D`：二维欧氏距离取整；
- `CEIL_2D`：二维欧氏距离向上取整；
- `ATT`：TSPLIB pseudo-Euclidean；
- `GEO`：TSPLIB 地理距离；
- `EXPLICIT`：`FULL_MATRIX`、行三角和含对角三角矩阵。

Loader 实现 TSPLIB 取整规则。独立验证检查 Hamiltonian permutation，并使用受治理源数据
重新计算闭合 tour 长度。

同一实例可以暴露 External Function tour cost 和 DAG IR transition-sum 等不同 model
style，它们是独立的能力和 GA comparison profile。

```bash
./.venv/bin/python benchmark.py list-cases --family sequence_blackbox_tsp
```
