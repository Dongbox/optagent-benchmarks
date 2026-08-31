# WTSDS 数据来源说明

WTSDS 目录保存 Weighted Tardiness Scheduling with Sequence-Dependent Setups 的公开 benchmark case，用于评估 OptAgent 在单机排列调度问题上的表现。

## 数据来源说明

WTSDS（Weighted Tardiness Scheduling with Sequence-Dependent Setups）由 Vincent A. Cicirello 发布，包含 120 个 60 作业实例、实例生成器和公开参考解。

数据集来源网站：

- WTSDS 实例库：https://www.cicirello.org/datasets/wtsds/
- 参考解来源：Tanaka 和 Araki 的公开 WTSDS 解表
- 本地实例目录：`benchmarks/cases/wtsdslib/wtsds/raw/wtsds-instances/`
- 本地参考解：`benchmarks/cases/wtsdslib/wtsds/raw/CicirelloSolution - CicirelloSolution.csv`

## 问题说明

给定单台机器上的全部作业。每个作业 `j` 具有处理时间 `p_j`、迟延权重 `w_j` 和到期日 `d_j`；从前序作业 `i` 切换到 `j` 需要准备时间 `s[i][j]`，第一个作业还需初始准备时间 `s[-1][j]`。

对任意排列 `π`，完工时间递推为：

```text
C[π[0]] = s[-1][π[0]] + p[π[0]]
C[π[k]] = C[π[k-1]] + s[π[k-1]][π[k]] + p[π[k]]
```

目标是最小化总加权迟延：

```text
sum(j, w[j] * max(0, C[j] - d[j]))
```

每个作业必须且只能执行一次；机器一次只能处理一个作业；准备时间位于前序作业结束与后继作业开始之间。

## 数据筛选依据

规模定义：`jobs` 为作业数量，是当前 WTSDS tier 分层的唯一规模指标。

- `jobs`：单台机器上必须排列的作业数；
- 核心规模指标为 jobs；
- 当前公开实例全部固定为 60 个作业。

tier 分类范围：

| tier | case 数量 | jobs 范围 |
|---|---:|---:|
| smoke | 0 | — |
| calibration | 120 | 60 |
| full | 0 | — |
| pressure | 0 | — |

筛选策略：当前不从完整候选集中抽样。已下载的 WTSDS 公开集恰好包含 120 个同规模实例，因此全部保留并统一登记为 `calibration`；未额外采用特征距离去重或分层筛选。

## 建模说明

建模方式：使用单机 `sequence_var` 表示作业排列；每个作业使用固定处理时长的 interval variable。`no_overlap` 保证机器容量，`sequence_setup` 根据初始准备时间和作业间准备时间精确约束 setup，`max(end - due, 0)` 表示作业迟延，目标为最小化其加权和。

适用的求解方式：

- `solve()`：适用；当前使用 GA 路径；
- `solve_cpsat()`：当前不适用，`sequence_setup` 尚未提供 CP-SAT lowering；
- `solve_milp()`：当前不适用，interval/sequence/setup 模型尚未提供 MILP lowering。

## 特殊备注

- 原始 `.instance` 文件列出 `-1 → job` 初始准备时间和所有 `i → j`（`i != j`）的作业间准备时间；未列出的对角线统一解释为 `s[i][i] = 0`。
- CSV 参考排列使用 0–59 的作业编号；当前注册值均标记为公开最优值，其中 22 个实例的最优目标为 0。
- 建模的 sequence default 为自然顺序 `0..59`，不使用公开参考排列作为初始解。
- 注册表是完整 case 清单的唯一权威来源，可通过 `python benchmark.py list-cases --tier calibration` 查询。

## 相关 case

### calibration

- `wtsdslib_wt_sds_1` 至 `wtsdslib_wt_sds_120`
  - 问题描述：60 个作业的单机序列相关准备时间加权迟延调度问题，目标是最小化总加权迟延。
  - 规模：`jobs=60`
  - 参考值性质：最优
  - 参考值/区间：每个算例在注册表中记录 `objective` 与对应公开排列；其中 22 个算例为 `objective=0`。
  - 备注：无

共 120 个 case。
