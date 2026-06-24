# Cases Series Refactor Adjustment

本文档用于梳理 `cases/` 下所有 case 的系列归并任务。目标不是再增加一层抽象，而是把一案一文件的实现，调整为按实例系列聚合的单文件模块：

```text
cases/<data_source>/<problem_type>/<instance_type>/<series>.py
```

每个系列文件应当自包含：

- 系列内全部 `BenchmarkCase` 声明；
- 默认策略声明与固定预算；
- `load_instance()`；
- `build_model()`；
- `solve_case()`；
- 必要时的系列内共享 helper。

旧的 per-instance 文件和顶层 family helper 已退出主路径，不保留兼容 shim。

## Current Inventory

当前 `cases/` 的公开实例大致分为 5 个 family：

- `jsplib/scheduling/jobshop`
- `tsplib/routing/tsp`
- `qaplib/assignment/quadratic_assignment`
- `psplib/scheduling/rcpsp`
- `miplib2017/exact/linear_mip`

现状已收敛为“系列文件 + raw/data.py”。每个系列文件直接承载 case 声明、默认策略、数据加载入口、建模和 `solve_case()`。

## Target Series Map

### JSPLIB Jobshop

目标系列文件：

| Current cases | Target series file | Notes |
| --- | --- | --- |
| `abz5`, `abz7` | `abz.py` | 已完成 |
| `ft06`, `ft10` | `ft.py` | 已完成 |
| `la16`, `la21` | `la.py` | 已完成 |
| `dmu01` | `dmu.py` | 已完成 |
| `swv01` | `swv.py` | 已完成 |

### TSPLIB TSP

目标系列文件：

| Current cases | Target series file | Notes |
| --- | --- | --- |
| `pr76` | `pr.py` | 单例系列 |
| `kroa100` | `kroa.py` | 单例系列 |
| `a280` | `a.py` | 单例系列 |
| `berlin52` | `berlin.py` | 单例系列 |
| `eil51` | `eil.py` | 单例系列 |

### QAPLIB Quadratic Assignment

目标系列文件：

| Current cases | Target series file | Notes |
| --- | --- | --- |
| `nug12`, `nug20` | `nug.py` | 已完成 |
| `had20` | `had.py` | 单例系列 |
| `lipa40a` | `lipa.py` | 单例系列 |
| `chr12a` | `chr.py` | 单例系列 |

### PSPLIB RCPSP

目标系列文件：

| Current cases | Target series file | Notes |
| --- | --- | --- |
| `j90_1_1`, `j90_1_8` | `j90_1.py` | 合并同一子系列 |
| `j90_2_4` | `j90_2.py` | 单例系列 |
| `j90_5_3` | `j90_5.py` | 单例系列 |
| `j90_6_7` | `j90_6.py` | 单例系列 |

### MIPLIB 2017 Exact Linear MIP

目标系列文件：

| Current cases | Target series file | Notes |
| --- | --- | --- |
| `reblock115` | `reblock.py` | 单例系列 |
| `air05` | `air.py` | 单例系列 |
| `fast0507` | `fast.py` | 单例系列 |
| `academictimetablesmall` | `academictimetable.py` | 已完成，采用稳定语义 stem |
| `case_50v_10` | `case_50v.py` | 单例系列 |
| `ran14x18_disj_8` | `ran14x18_disj.py` | 单例系列 |

## Refactor Rules

1. 系列文件优先，不再以单个实例编号作为主模块组织方式。
2. 系列文件内可保留重复逻辑，不强求跨系列抽 helper。
3. 系列文件中的 case 对象应显式命名，例如 `FT06`、`FT10`、`J90_1_1`。
4. `CASES` 必须只由当前系列文件暴露的 case 组成。
5. 系列级 `solve_case()` 必须能独立调用，不依赖顶层 `cases/*_model.py` / `cases/*_solve.py`。
6. 原 `cases/<source>/<problem_type>/<instance_type>/<instance>.py` 不保留 shim。
7. `__init__.py` 只聚合系列文件，不再聚合单个实例文件。

## Completed Waves

### Wave 1: JSPLIB Jobshop

- `abz.py`、`ft.py`、`la.py`、`dmu.py`、`swv.py` 均已承载各自系列声明、建模和默认求解。
- 已删除 `ft06.py`、`ft10.py`、`la16.py`、`la21.py`、`dmu01.py`、`swv01.py`。
- `cases/jsplib/scheduling/jobshop/__init__.py` 只聚合系列文件。

### Wave 2: TSPLIB TSP

- `pr.py`、`kroa.py`、`a.py`、`berlin.py`、`eil.py` 已承载对应 case 声明、建模和默认策略。
- 已删除 `pr76.py`、`kroa100.py`、`a280.py`、`berlin52.py`、`eil51.py`。
- `cases/tsplib/routing/tsp/__init__.py` 只聚合系列文件。

### Wave 3: QAPLIB

- `nug.py`、`had.py`、`lipa.py`、`chr.py` 已承载对应 case 声明、建模和默认策略。
- `nug12` / `nug20` 已合并到 `nug.py`。
- 已删除旧单实例模块。

### Wave 4: PSPLIB RCPSP

- `j90_1.py`、`j90_2.py`、`j90_5.py`、`j90_6.py` 已承载对应 case 声明、建模和默认策略。
- `j90_1_1` / `j90_1_8` 已合并到 `j90_1.py`。
- 已删除旧单实例模块。

### Wave 5: MIPLIB 2017

- 已新增 `reblock.py`、`air.py`、`fast.py`、`academictimetable.py`、`case_50v.py`、`ran14x18_disj.py` 并迁移 exact baseline flow。
- 保留 `exact/linear_mip` 层级不变，策略仍决定求解方式。
- 已删除旧单实例模块。

### Wave 6: Cleanup

- 已删除旧单实例模块，不保留 shim。
- 已删除 `cases/jsplib_jobshop.py`、`cases/jsplib_jobshop_model.py`、`cases/tsplib_tsp.py`、`cases/tsplib_tsp_model.py`、`cases/tsplib_tsp_graph_model.py`、`cases/qaplib_quadratic_assignment.py`、`cases/qaplib_quadratic_assignment_model.py`、`cases/psplib_rcpsp.py`、`cases/psplib_rcpsp_model.py`、`cases/miplib2017_linear_mip.py`、`cases/miplib2017_linear_mip_model.py`。
- 已更新 `cases/registry.py`，仅按 `case_module` 路由到系列模块的 `solve_case()`。
- 已跑 focused compile、list-cases、direct smoke 和 suite inventory smoke。

## Acceptance Criteria

- 每个 family 的公开实例入口从“单实例文件列表”收敛为“系列文件列表”。
- `python -m benchmarks.run --list-cases` 仍能列出完整 case 集合。
- 每个系列文件都可独立承载默认求解流程。
- 不再依赖旧的顶层 `models/`、`loaders/` 风格组织。
- 不保留旧实例文件兼容路径。

## Validation

- `python -m compileall cases`
- `python -m benchmarks.run --list-cases`
- `python -m benchmarks.run --case tsplib_berlin52 --strategy local_search --no-download --max-iterations 1 --time-limit-s 0.1 --no-exact-baseline`
- `python -m benchmarks.run --case qaplib_nug12 --strategy local_search --no-download --max-iterations 1 --time-limit-s 0.1 --no-exact-baseline`
- `python -m benchmarks.run --case jsplib_ft06 --strategy local_search --no-download --max-iterations 1 --time-limit-s 0.1 --no-exact-baseline`
- `python -m benchmarks.run --case psplib_j90_1_1 --strategy local_search --no-download --max-iterations 1 --time-limit-s 0.1 --no-exact-baseline`
- `python -m benchmarks.run --case miplib2017_50v-10 --strategy optx --no-download --time-limit-s 0.1`
- `python -m benchmarks.runners.run --list-inventory --family sequence_blackbox_tsp --tier smoke --timestamp case-series-refactor-smoke`
