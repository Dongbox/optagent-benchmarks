# Phase 5: Legacy Cleanup

## Goal

完成统一接口迁移后，删除旧路径和兼容负担，让 case 开发模型稳定下来。

阶段完成后：

- `run.py` 是唯一求解主流程入口。
- case 文件只保留 case 声明、`build_model()` 和可选 `solution_summary()`。
- registry 只负责发现和返回 case，不再负责调用系列级 `solve_case()`。
- 文档和测试都以新接口为准。

## Scope

### In Scope

- 删除或降级系列级 `solve_case()`。
- 删除 case 文件中的 `StrategyDeclaration`、默认 strategy tuple 和私有 budget dataclass。
- 删除 `*BenchmarkModel` wrapper。
- 清理 `load_instance()` 作为公开接口的残留。
- 更新旧架构文档中与新接口冲突的内容。
- 增加防回归检查。

### Out Of Scope

- 不删除 raw data parser。
- 不重写 dashboard 历史结果。
- 不改变 case 目录系列组织方式。

## Cleanup Tasks

### Registry

目标：

- `benchmark_cases()` 继续返回 rows，兼容 list/inventory。
- 新增或保留返回 `BenchmarkCase` 对象的 lookup。
- `run_case()` 不再导入系列模块调用 `solve_case()`；应委托 `run.py` 的统一执行函数，或被移除。

任务：

1. 搜索 `registry.run_case()` 调用方。
2. 将调用方迁移到 `run.py` 统一入口。
3. 删除 `_accepts_instance_argument()` 这类只为兼容 `solve_case()` 签名存在的逻辑。

### Case Files

对每个 family 执行：

```bash
rg -n "class .*BenchmarkModel|-> .*BenchmarkModel|def load_instance|default_strategies|StrategyDeclaration|def solve_case|StrategyBudget" cases
```

处理规则：

- `*BenchmarkModel`：删除。
- `load_instance()`：如果只被 `build_model()` 使用，可以改为私有 helper；不再作为 runner contract。
- `StrategyDeclaration` / default strategies：删除，迁移到 `run.py`。
- `solve_case()`：删除，或明确标记为 legacy shim 并计划后续删除。
- 私有 budget dataclass：删除，使用 `run.py.LocalRunBudget` 或统一 budget 类型。

### Documentation

需要更新：

- `docs/case-architecture-refactor.md`
- `docs/cases-series-refactor-adjustment.md`
- `docs/presentation-runner-dashboard-refactor.md`
- 任何仍描述 `build_model() -> Any`、case 级 `load_instance()`、case 级默认策略或系列级 `solve_case()` 为目标架构的内容。

### Regression Tests

建议增加检查：

- 所有 public case 的 `build_model()` 返回 `ModelBuilder`。
- public case 不要求实现 `load_instance()`。
- case 源码不定义 `class .*BenchmarkModel`。
- case 源码不定义新增 `StrategyDeclaration`。
- `run.py` 能对每个 implemented family 至少选择一个 case 执行 smoke。

## Acceptance Criteria

- `rg -n "class .*BenchmarkModel|-> .*BenchmarkModel" cases` 无有效命中。
- `rg -n "default_strategies|StrategyDeclaration|StrategyBudget" cases` 无目标实现命中。
- `rg -n "def solve_case" cases` 无目标实现命中，或只剩明确标记的 legacy shim。
- `BenchmarkCase` 目标接口和文档一致。
- 所有 implemented family 的 smoke case 通过。
- dashboard data check 通过。

## Validation

```bash
python -m compileall cases presentation run.py
PYTHONPATH=.. python -m benchmarks.run --list-cases
PYTHONPATH=.. python -m benchmarks.run --case tsplib_berlin52 --strategy local_search --no-download --max-iterations 1 --time-limit-s 0.1
PYTHONPATH=.. python -m benchmarks.run --case qaplib_nug12 --strategy local_search --no-download --max-iterations 1 --time-limit-s 0.1
PYTHONPATH=.. python -m benchmarks.run --case jsplib_ft06 --strategy local_search --no-download --max-iterations 1 --time-limit-s 0.1
PYTHONPATH=.. python -m benchmarks.run --case psplib_j90_1_1 --strategy local_search --no-download --max-iterations 1 --time-limit-s 0.1
PYTHONPATH=.. python -m benchmarks.run --case miplib2017_50v-10 --strategy optx --no-download --time-limit-s 0.1
PYTHONPATH=.. python -m benchmarks.presentation.generate_dashboard_data --check
```
