# Phase 3: Migrate Simple Families

## Goal

先迁移 wrapper 较简单的 family，让一批 case 完全走统一 `run.py` 路径。

本阶段目标 family：

- TSPLIB TSP
- QAPLIB Quadratic Assignment
- MIPLIB 2017 Linear MIP

## Scope

### In Scope

- 删除或旁路 `TspBenchmarkModel`、`QapBenchmarkModel`、`MipBenchmarkModel`。
- 将 case 子类 `build_model()` 改为返回 `ModelBuilder`。
- 将实例加载收进 `build_model()` 内部。
- 将结果解析迁到 `solution_summary()`。
- 移除这些 family 中新增路径对 `solve_case()`、case 级策略声明和私有 budget 的依赖。

### Out Of Scope

- 不迁移 JSPLIB 和 PSPLIB。
- 不删除历史兼容入口，除非已无调用方。
- 不重构 raw data parser。

## TSPLIB TSP Tasks

目标：

- `build_model()` 返回 `ModelBuilder`。
- route/tour 变量使用稳定名称，例如 `tour`。
- `solution_summary()` 使用 `solution.value("tour")` 或等价公开 API 读取序列。
- 目标值优先从 `solution.objective` 读取；如果 OptAgent objective 与 TSPLIB evaluator 表达有差异，可在 `solution_summary()` 内部重新加载实例并复算。

具体任务：

1. 在一个 TSPLIB 系列文件上做竖切，例如 `cases/tsplib/routing/tsp/berlin.py`。
2. 删除新路径对 `TspBenchmarkModel.program`、`sequence_node_id`、`default_tour`、`instance` 的依赖。
3. 将 `_run_strategy()` 逻辑迁到 `run.py` 或让该 case 走 `run.py` 通用 runner。
4. 保留 `model_style` 作为普通 `build_model(model_style=...)` 参数；只有需要 result row 输出时才由 `run.py` 或 summary 返回。
5. 验证 `sequence_head`、`dimension`、`edge_weight_type` 等领域字段仍可输出。

验收：

- `rg -n "TspBenchmarkModel" cases/tsplib/routing/tsp/berlin.py` 无命中。
- `berlin52` 可通过 `run.py` 通用路径求解。

## QAPLIB Tasks

目标：

- `build_model()` 返回 `ModelBuilder`。
- assignment 变量使用稳定名称，例如 `assignment`。
- `solution_summary()` 使用变量名读取 assignment。
- QAP objective 可从 solution 或本地 evaluator 复算。

具体任务：

1. 选择 `nug.py` 作为多实例系列竖切。
2. 删除新路径对 `QapBenchmarkModel.program`、`assignment_node_id`、`default_assignment`、`instance` 的依赖。
3. 将 external callback 相关的 callback context 保持在建模内部。
4. 迁移 `_run_strategy()` 的 result row 拼装到 `run.py`。
5. 验证 `assignment_head`、`size`、objective/gap 字段。

验收：

- `rg -n "QapBenchmarkModel" cases/qaplib/assignment/quadratic_assignment/nug.py` 无命中。
- `qaplib_nug12` 可通过 `run.py` 通用路径求解。

## MIPLIB Tasks

目标：

- `build_model()` 返回 `ModelBuilder`。
- 变量使用 MPS 变量名作为 OptAgent 变量名。
- `solution_summary()` 只输出基础 solver 字段和必要 MIP 规模字段。
- exact route 仍由 `run.py` 统一选择策略和求解函数。

具体任务：

1. 选择一个小 MIP case 做竖切，例如 `case_50v.py`。
2. 删除新路径对 `MipBenchmarkModel.program`、`variable_node_ids`、`instance` 的依赖。
3. 确认 `solve(ModelBuilder, strategy=MilpConfig)` 是否覆盖当前 `solve_milp` 能力。
4. 如果 exact solve 仍需 `solve_milp`，只在 `run.py` 做策略分发，不把特殊求解逻辑留在 case 文件。
5. 验证 MIP result row 中 `variables`、`constraints`、`nonzeros`、objective/status 字段。

验收：

- `rg -n "MipBenchmarkModel" cases/miplib2017/exact/linear_mip/case_50v.py` 无命中。
- `miplib2017_50v-10` 可通过统一入口运行。

## Acceptance Criteria

- 三个 family 至少各有一个 case 完成通用路径迁移。
- 已迁移 case 不再向 runner 暴露内部实例数据类型。
- 已迁移 case 不再返回 `*BenchmarkModel`。
- 已迁移 case 的策略构造和 result row 拼装由 `run.py` 完成。
- metadata 没有变成大段样板；只有必要时保留少量 summary bridge。

## Validation

```bash
python -m compileall cases presentation run.py
PYTHONPATH=.. python -m benchmarks.run --case tsplib_berlin52 --strategy local_search --no-download --max-iterations 1 --time-limit-s 0.1
PYTHONPATH=.. python -m benchmarks.run --case qaplib_nug12 --strategy local_search --no-download --max-iterations 1 --time-limit-s 0.1
PYTHONPATH=.. python -m benchmarks.run --case miplib2017_50v-10 --strategy optx --no-download --time-limit-s 0.1
PYTHONPATH=.. python -m benchmarks.presentation.generate_dashboard_data --check
```
