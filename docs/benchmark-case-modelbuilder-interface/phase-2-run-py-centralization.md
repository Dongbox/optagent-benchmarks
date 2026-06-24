# Phase 2: Centralize `run.py`

## Goal

将求解主流程集中到根目录 `run.py`：

1. 解析用户参数。
2. 选择 case。
3. 构造 OptAgent 策略配置。
4. 调用 `case.build_model(...)` 得到 `ModelBuilder`。
5. 直接调用 `optagent.solve(model_builder, strategy=...)`。
6. 调用 `case.solution_metrics(solution)`。
7. 拼装 result row。

阶段完成后，至少一个 smoke case 可以完全不经过系列级 `solve_case()` 完成求解。

## Scope

### In Scope

- 在 `run.py` 中新增统一执行函数。
- 在 `run.py` 中集中维护 strategy name 到 OptAgent config 的映射。
- 在 `run.py` 中集中处理 budget、seed、time limit、trace、elapsed time。
- 将 result row 基础字段拼装迁移到 `run.py`。
- 保留旧 `registry.run_case()` 和系列 `solve_case()` 作为兼容路径。

### Out Of Scope

- 不在本阶段迁移全部 family。
- 不改变 dashboard JSON schema。
- 不要求删除 case 文件中的旧策略声明。

## Target `run.py` Shape

新增统一函数示意：

```python
def run_benchmark_case(
    case: BenchmarkCase,
    *,
    strategies: tuple[str, ...] | None = None,
    allow_download: bool = True,
    budget: LocalRunBudget | None = None,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    effective_budget = budget or LocalRunBudget()
    strategy_names = strategies or default_strategy_names_for_family(case.family)
    rows = []
    for strategy_name in strategy_names:
        model = case.build_model(allow_download=allow_download, **kwargs)
        strategy_config = build_strategy_config(case=case, strategy_name=strategy_name, budget=effective_budget)
        started = perf_counter()
        try:
            solution = solve(model, strategy=strategy_config, seed=effective_budget.seed, time_limit_s=effective_budget.time_limit_s)
            elapsed_seconds = perf_counter() - started
            solver_summary = solver_solution_summary(solution)
            case_metrics = case.solution_metrics(solution, **kwargs)
            rows.append(build_result_row(case, strategy_name, strategy_config, solver_summary, case_metrics, elapsed_seconds))
        except Exception as exc:
            rows.append(build_error_row(case, strategy_name, exc, perf_counter() - started))
    return rows
```

## Strategy Mapping

`run.py` 统一维护策略名称：

- `ga` -> `GaConfig`
- `advanced_ga` -> `AdvancedGaConfig`
- `alns` -> `AlnsConfig`
- `tabu` -> `TabuConfig`
- `local_search` -> `LocalSearchConfig`
- `lns` -> `LnsConfig`
- `optx` / `milp` -> `MilpConfig` 或 exact solve route

要求：

- case 文件不声明默认策略。
- family 级默认策略由 `run.py` 维护，例如 `default_strategy_names_for_family(family)`。
- 特定 strategy 需要 family 参数时，`run.py` 可以读取 `case.family`、`case.size`、CLI budget 和普通 kwargs。

## Result Row Contract

`run.py` 拼装基础字段：

- `kind`
- `benchmark_id`
- `family`
- `tier`
- `instance`
- `strategy`
- `strategy_profile`
- `strategy_config`
- `solver_name`
- `status`
- `feasible`
- `objective`
- `reference_objective`
- `reference_kind`
- `gap_abs`
- `gap_rel`
- `elapsed_seconds`
- `time_to_best_seconds`
- `metadata`

case 的 `solution_metrics()` 只补充领域 correctness / audit facts，例如：

- `objective`
- `raw_objective`
- `reference_objective`
- `decoded_solution`
- 领域诊断 `metadata`
- 动态 `model_style`

`run.py` 统一读取 `solver_name`、`status`、`feasible` 和 solution metadata。case metrics
只允许覆盖明确列出的领域字段，尤其是 `objective`，因为 TSP/QAP 等 family 可能需要用
领域 evaluator 复算目标值。`sequence_head`、`activity_start_head`、`dimension`、
`edge_weight_type` 等展示字段由 `presentation/` 派生。

## Registry Transition

迁移期策略：

- `registry.benchmark_cases()` 继续收集 case rows。
- 新增 `registry.case_by_id()` 或复用 `run.py.case_by_id()` 返回 `BenchmarkCase` 对象。
- `registry.run_case()` 可以先委托旧系列 `solve_case()`，再逐步切到 `run.run_benchmark_case()`。
- presentation suite 在本阶段不强制改路由。

## Implementation Steps

1. 在 `run.py` 新增 strategy config builder。
2. 在 `run.py` 新增 default strategy name mapping。
3. 在 `run.py` 新增 result row builder 和 error row builder。
4. 在 `run.py` 新增 `run_benchmark_case()`。
5. 选择一个小 case 接入通用路径，建议 TSPLIB `berlin52` 或 QAPLIB `nug12`。
6. 对比旧路径和新路径输出字段，确认 dashboard contract 未破坏。

## Acceptance Criteria

- `run.py` 可以直接执行至少一个 `case.build_model()` + `solve(ModelBuilder)` + `case.solution_summary()` 路径。
- 新路径不调用系列级 `solve_case()`。
- 新路径不接收或传递 `TspInstance`、`QapInstance`、`*BenchmarkModel` 等自定义对象。
- result row 至少包含现有 dashboard 所需基础字段。

## Validation

```bash
python -m compileall cases presentation run.py
PYTHONPATH=.. python -m benchmarks.run --list-cases
PYTHONPATH=.. python -m benchmarks.run --case tsplib_berlin52 --strategy local_search --no-download --max-iterations 1 --time-limit-s 0.1
PYTHONPATH=.. python -m benchmarks.presentation.generate_dashboard_data --check
```
