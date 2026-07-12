# MIPLIB 2017

该数据源包含 MIPLIB 2017 中选定的线性混合整数规划实例，用于精确 MIP 能力验证，不是
启发式搜索主 family。

Case 加载受治理的 MPS 证据，保留变量整数性和线性约束，并按模型声明最小化或最大化
线性目标。Reference 记录 optimum 或带来源的 best-known bound。

大型原始文件可下载到 `linear_mip/raw/`；只有获准离线再分发的 release-gate 证据可以
提交。精确结果必须保留实际 backend 名称和版本。

```bash
./.venv/bin/python benchmark.py list-cases --family exact_linear_mip
```
