# Phase 1: Interface Contract

## Goal

固定 `BenchmarkCase` 的最小接口，让 case 层只暴露建模和 solution 解析能力。

阶段完成后，新增 case 的最小实现应只需要：

- case metadata；
- `build_model(**kwargs) -> ModelBuilder`；
- 可选 `solution_summary(solution, **kwargs)`。

## Scope

### In Scope

- 修改 `cases/base.py` 中 `BenchmarkCase.build_model()` 的类型和语义。
- 新增 `BenchmarkCase.solution_summary()` 和 `default_solution_summary()`。
- 从目标接口中移除 `load_instance()`。
- 从目标 case contract 中移除 `default_strategies` / `StrategyDeclaration`。
- 明确 `build_model()` 返回 `optagent.ModelBuilder`，不返回 `*BenchmarkModel`。
- 建立 metadata 最小化原则。

### Out Of Scope

- 不在本阶段迁移所有 case 文件。
- 不删除现有 `solve_case()`，只把它降级为迁移期兼容路径。
- 不重写 result row 或 dashboard contract。

## Target Changes

### `cases/base.py`

将基类目标接口调整为：

```python
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

处理原则：

- `load_instance()` 不再作为新增 case 的基类接口；如果为兼容保留，应标记为 legacy。
- `StrategyDeclaration` 可以迁移期保留给旧 case 使用，但不再是目标设计的一部分。
- `CaseDeclaration`、`case_to_row()`、`ensure_benchmark_case()` 应继续兼容现有 registry 和 dashboard 读取。

### Case Implementation Guidance

case 子类示例：

```python
class TspCase(BenchmarkCase):
    def build_model(self, **kwargs: Any) -> ModelBuilder:
        instance_data = load_tsp_case(self.to_row(), cache_dir=RAW_DIR, allow_download=kwargs.get("allow_download", True))
        builder = ModelBuilder()
        tour = builder.sequence_var(size=instance_data.dimension, default=list(range(instance_data.dimension)), name="tour")
        builder.minimize(...)
        return builder

    def solution_summary(self, solution: Any, **kwargs: Any) -> dict[str, Any]:
        sequence = [int(item) for item in solution.value("tour")]
        return {**super().solution_summary(solution, **kwargs), "sequence_head": sequence[:20]}
```

## Metadata Rule

默认不写 `ModelBuilder.metadata`。

允许写入的情况：

- model style 影响同一 case 的对比维度，且无法从 `case.series_key` 或运行参数判断；
- `solution_summary()` 无法通过变量名或公开 solution API 读取必要字段；
- 需要少量机器可读桥接字段。

禁止写入的情况：

- 重复 `benchmark_id`、`family`、`source`、`tier`、`reference`、`size` 等 case 已有字段；
- 长篇建模说明；
- 为替代清晰变量名而记录大量 node id。

## Implementation Steps

1. 在 `cases/base.py` 中引入 `ModelBuilder` 类型注解；如直接 import 会导致依赖问题，可用 `TYPE_CHECKING` 或字符串注解。
2. 修改 `BenchmarkCase.build_model()` 签名为 `def build_model(self, **kwargs: Any) -> ModelBuilder`。
3. 增加 `solution_summary()` 和 `default_solution_summary()`。
4. 将 `load_instance()` 标记为 legacy 或从目标文档中移除；本阶段不强制删除旧 case 依赖。
5. 增加轻量防回归检查，确认新目标接口文档与 `cases/base.py` 一致。

## Acceptance Criteria

- `BenchmarkCase.build_model()` 类型语义明确为返回 `ModelBuilder`。
- `BenchmarkCase` 有默认 `solution_summary()`。
- 新增 case 不需要实现 `load_instance()`。
- 文档中不再把 `StrategyDeclaration`、`default_strategies` 或 `solve_case()` 作为新增 case 目标接口。

## Validation

```bash
python -m compileall cases
PYTHONPATH=.. python -m benchmarks.run --list-cases
```
