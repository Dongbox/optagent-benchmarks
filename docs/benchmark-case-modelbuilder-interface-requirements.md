# BenchmarkCase ModelBuilder Interface Roadmap

本文档是 `BenchmarkCase` 建模接口重构的总入口。详细开发任务按阶段拆分到 `docs/benchmark-case-modelbuilder-interface/` 下的独立文档中。

## Problem

当前 `BenchmarkCase` 和各 case 系列模块的职责边界过宽：

- `BenchmarkCase.build_model()` 返回 `Any`，无法表达“这是 OptAgent 可直接求解的模型”。
- `load_instance()` 暴露在基类接口上，使 runner 需要理解 case 内部数据加载细节。
- case 文件维护 `StrategyDeclaration`、默认 budget 和系列级 `solve_case()`，导致求解流程散落在各系列模块。
- 大量 `TspBenchmarkModel`、`JobShopBenchmarkModel`、`QapBenchmarkModel`、`RcpspBenchmarkModel`、`MipBenchmarkModel` 等 wrapper 只是在传递 OptAgent program、node id、实例数据和后处理字段。
- 建模代码里过多 metadata 会影响可读性，且许多字段已经存在于 `BenchmarkCase` metadata 中。

## Target Architecture

目标是把 case 与 runner 的边界收敛为三个动作：

```python
case.to_row() -> dict[str, Any]
case.build_model(**primitive_kwargs) -> optagent.ModelBuilder
case.solution_summary(solution, **primitive_kwargs) -> dict[str, Any]
```

核心原则：

- case 只负责建模和解释 solution。
- 实例加载、下载、raw data 解析都封装在 `build_model()` 内部。
- `build_model()` 返回 `ModelBuilder`；根目录 `run.py` 直接调用 `optagent.solve(model_builder, strategy=...)`，由 `solve()` 内部执行 freeze。
- 策略声明、budget 解析、CLI 参数、求解主流程和 result row 拼装统一放到根目录 `run.py`。
- `solution_summary()` 优先通过 OptAgent solution 的公开字段和变量名读取结果。
- 默认不写 `ModelBuilder.metadata`；只有 solution 解析缺少必要桥接信息时才写少量 metadata。
- runner 与 case 边界不传递 benchmark 自定义实例类型、wrapper 类型或系列私有 budget 类型。

## Target `BenchmarkCase` Shape

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from optagent import ModelBuilder


@dataclass(frozen=True)
class BenchmarkCase:
    benchmark_id: str
    source: str
    problem_type: str
    instance_type: str
    instance: str
    family: str
    tier: str
    compare_key: str
    series_key: str
    size: Mapping[str, Any]
    data: Mapping[str, Any]
    reference: Mapping[str, Any]
    problem_description: str
    case_module: str
    modeling_notes: Mapping[str, Any] = field(default_factory=dict)
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    def build_model(self, **kwargs: Any) -> ModelBuilder:
        raise NotImplementedError

    def solution_summary(self, solution: Any, **kwargs: Any) -> dict[str, Any]:
        return self.default_solution_summary(solution)

    def default_solution_summary(self, solution: Any) -> dict[str, Any]:
        return {
            "solver_name": getattr(solution, "solver_name", None),
            "status": getattr(getattr(solution, "status", None), "value", str(getattr(solution, "status", ""))),
            "feasible": bool(getattr(solution, "feasible", False)),
            "objective": getattr(solution, "objective", None),
        }
```

明确移出 case 目标接口：

- `load_instance()`：实例加载属于 `build_model()` 内部建模细节。
- `default_strategies` / `StrategyDeclaration`：策略声明由 `run.py` 统一定义。
- 系列级 `solve_case()`：求解流程由 `run.py` 统一编排。
- `*BenchmarkModel` wrapper：不再用系列私有 dataclass 包装 OptAgent 对象。

## Phase Documents

按以下顺序执行，每个阶段必须独立验收后再进入下一阶段。

| Phase | Document | Goal |
| --- | --- | --- |
| 1 | [phase-1-interface-contract.md](benchmark-case-modelbuilder-interface/phase-1-interface-contract.md) | 固定 `BenchmarkCase` 最小接口，移除 `load_instance()`、case 级策略声明和 wrapper 返回值。 |
| 2 | [phase-2-run-py-centralization.md](benchmark-case-modelbuilder-interface/phase-2-run-py-centralization.md) | 将策略构造、求解主流程和 result row 拼装集中到根目录 `run.py`。 |
| 3 | [phase-3-simple-families.md](benchmark-case-modelbuilder-interface/phase-3-simple-families.md) | 先迁移 TSPLIB、QAPLIB、MIPLIB 这类 wrapper 较简单的 family。 |
| 4 | [phase-4-scheduling-families.md](benchmark-case-modelbuilder-interface/phase-4-scheduling-families.md) | 迁移 JSPLIB job-shop 和 PSPLIB RCPSP 等后处理更复杂的排程 family。 |
| 5 | [phase-5-legacy-cleanup.md](benchmark-case-modelbuilder-interface/phase-5-legacy-cleanup.md) | 删除旧入口、清理兼容路径、更新文档和防回归检查。 |

## Global Acceptance Criteria

- `BenchmarkCase.build_model()` 返回 OptAgent 公共可求解对象，目标类型为 `ModelBuilder`。
- `BenchmarkCase` 目标接口不包含 `load_instance()`。
- 根目录 `run.py` 直接将 `ModelBuilder` 传给 `optagent.solve()`，不显式执行 freeze。
- 每个 case 文件不再需要定义 `JobShopBenchmarkModel`、`TspBenchmarkModel` 等自定义 wrapper。
- 每个 case 文件不再声明默认求解策略、默认 budget 或新增系列级求解主函数。
- `run.py` 与 case 类交互时不传递 benchmark 自定义数据类型。
- 建模代码不重复维护大段 metadata；metadata 只作为必要时的最小桥接信息。
- result row、dashboard index 和 aggregates 的数据合同保持兼容。
- 现有 case inventory 不减少。
- 每个 family 至少有一个 smoke case 通过。

## Global Validation Commands

从 `benchmarks/` 目录执行：

```bash
python -m compileall cases presentation
PYTHONPATH=.. python -m benchmarks.run --list-cases
PYTHONPATH=.. python -m benchmarks.run --case tsplib_berlin52 --strategy local_search --no-download --max-iterations 1 --time-limit-s 0.1
PYTHONPATH=.. python -m benchmarks.run --case qaplib_nug12 --strategy local_search --no-download --max-iterations 1 --time-limit-s 0.1
PYTHONPATH=.. python -m benchmarks.run --case jsplib_ft06 --strategy local_search --no-download --max-iterations 1 --time-limit-s 0.1
PYTHONPATH=.. python -m benchmarks.run --case psplib_j90_1_1 --strategy local_search --no-download --max-iterations 1 --time-limit-s 0.1
PYTHONPATH=.. python -m benchmarks.run --case miplib2017_50v-10 --strategy optx --no-download --time-limit-s 0.1
PYTHONPATH=.. python -m benchmarks.presentation.generate_dashboard_data --check
```

## Open Questions

- `solution.value("variable_name")` 或等价公开 API 是否已经覆盖所有 summary 场景？若覆盖，应避免为 node id 额外写 metadata。
- MIPLIB exact flow 当前使用 `solve_milp`，是否能和 `solve(ModelBuilder, strategy=MilpConfig)` 完全统一？如果不能，`run.py` 应保留最小策略分发，但 case 侧仍只返回 `ModelBuilder`。
