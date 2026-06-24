# Phase 4: Migrate Scheduling Families

## Goal

迁移后处理更复杂的 scheduling family：

- JSPLIB job-shop
- PSPLIB RCPSP

本阶段重点不是抽象排程逻辑，而是移除私有 `*BenchmarkModel` wrapper，让 case 文件同样只暴露 `build_model()` 和 `solution_summary()`。

## Scope

### In Scope

- 删除或旁路 `JobShopBenchmarkModel` 和 `RcpspBenchmarkModel`。
- 将实例加载封装进 `build_model()`。
- 用稳定变量命名支持 solution 解析。
- 将 makespan、operation start、machine order、activity start 等领域摘要放入 `solution_summary()`。
- 将策略构造、budget 和 result row 拼装交给 `run.py`。

### Out Of Scope

- 不重写 job-shop 或 RCPSP 建模数学形式。
- 不强制跨 JSPLIB 和 PSPLIB 抽象公共 scheduling helper。
- 不改变 raw data 文件格式。

## JSPLIB Job-Shop Tasks

目标：

- `build_model()` 返回 `ModelBuilder`。
- operation start、machine order、makespan 等变量有稳定名称。
- `solution_summary()` 可以输出 makespan、operation head 和 machine order head。

建议变量命名：

```text
start_j{job}_o{operation}
machine_order_m{machine}
makespan
```

具体任务：

1. 选择 `ft.py` 做第一条竖切，优先 `ft06` smoke。
2. 将 `JobShopCase.build_model()` 改为直接返回 `ModelBuilder`。
3. 将实例读取留在 `build_model()` 内部，不暴露给 runner。
4. 删除新路径对 `JobShopBenchmarkModel.program`、`operation_node_ids`、`machine_sequence_node_ids`、`objective_node_id`、`instance` 的依赖。
5. 将 `makespan_from_solution()`、`operation_start_head()`、`_machine_order_head()` 等 helper 调整为接受 OptAgent solution 和普通参数。
6. 让 `solution_summary()` 返回现有 result row 依赖的领域字段。
7. 完成 `ft.py` 后按系列推广到 `abz.py`、`la.py`、`dmu.py`、`swv.py`。

验收：

- `rg -n "JobShopBenchmarkModel" cases/jsplib/scheduling/jobshop` 对已迁移文件无命中。
- `jsplib_ft06` 通过 smoke。
- 输出仍包含 makespan 或等价 objective 字段。

## PSPLIB RCPSP Tasks

目标：

- `build_model()` 返回 `ModelBuilder`。
- activity start 和 objective/makespan 变量有稳定名称。
- `solution_summary()` 可以输出 makespan 和 activity start head。

建议变量命名：

```text
start_a{activity}
makespan
```

具体任务：

1. 选择 `j90_1.py` 做第一条竖切，优先 `j90_1_1` smoke。
2. 将 `RcpspCase.build_model()` 改为直接返回 `ModelBuilder`。
3. 将实例读取留在 `build_model()` 内部。
4. 删除新路径对 `RcpspBenchmarkModel.program`、`activity_node_ids`、`objective_node_id`、`horizon`、`instance` 的依赖。
5. 将 `makespan_from_solution()`、`activity_start_head()` 调整为接受 OptAgent solution。
6. 让 `solution_summary()` 返回现有 result row 依赖的领域字段。
7. 完成 `j90_1.py` 后推广到 `j90_2.py`、`j90_5.py`、`j90_6.py`。

验收：

- `rg -n "RcpspBenchmarkModel" cases/psplib/scheduling/rcpsp` 对已迁移文件无命中。
- `psplib_j90_1_1` 通过 smoke。
- 输出仍包含 activity start 摘要或等价字段。

## Metadata Guidance

优先通过稳定变量名读取 solution。

只有以下情况允许少量 metadata：

- 变量集合无法通过命名规则恢复；
- OptAgent solution 暂不支持按变量名读取；
- 领域摘要必须知道非变量的建模参数，且该参数无法从 `case.size` 或 `case.reference` 获得。

如果 metadata 超过少量键值，应回头调整变量命名或 solution API 使用方式。

## Acceptance Criteria

- JSPLIB 至少一个系列完成通用路径迁移。
- PSPLIB 至少一个系列完成通用路径迁移。
- 已迁移 scheduling case 不再返回 `JobShopBenchmarkModel` 或 `RcpspBenchmarkModel`。
- `run.py` 统一负责策略和 result row 基础字段。
- `solution_summary()` 负责领域摘要，不把领域内部对象传给 runner。

## Validation

```bash
python -m compileall cases presentation run.py
PYTHONPATH=.. python -m benchmarks.run --case jsplib_ft06 --strategy local_search --no-download --max-iterations 1 --time-limit-s 0.1
PYTHONPATH=.. python -m benchmarks.run --case psplib_j90_1_1 --strategy local_search --no-download --max-iterations 1 --time-limit-s 0.1
PYTHONPATH=.. python -m benchmarks.presentation.generate_dashboard_data --check
```
