# Solution Metrics and Presentation Boundary

本文档固定 `BenchmarkCase` 解读 solution、`run.py` 拼装 result row、`presentation/` 生成展示数据之间的职责边界。

## Problem

当前 case 侧的 `solution_summary()` 同时承担了三类职责：

- 读取 OptAgent solution 的通用求解字段，例如 `solver_name`、`status`、`feasible`、`metadata`。
- 根据 case 建模上下文解码领域结果，例如 TSP tour、QAP assignment、job-shop operation start 或 machine order。
- 为 dashboard 或本地报告输出展示派生字段，例如 `sequence_head`、`machine_order_head`、`dimension`、`edge_weight_type`。

这会让 case 文件变成 dashboard row schema 的维护点，也会鼓励新增 case 时把展示字段手工写进 `_domain.py`。长期看，case 和 presentation 的边界会继续变宽。

## Target Boundary

目标边界如下：

- `cases/` 负责声明 benchmark case、构建 OptAgent model，并解释 solution 中只有 case 才知道的领域事实。
- `run.py` 负责统一求解流程、读取 solver 通用字段、计算 gap，并拼装标准 result row。
- `presentation/` 负责 dashboard、本地报告和发布所需的派生展示字段、截断字段、聚合字段和格式化。

换句话说，case 可以告诉 runner “这个 solution 在本问题上的 objective 是多少、领域变量是什么”；presentation 再决定 “界面上展示前 20 个元素、按什么 label 命名、怎么聚合”。

## Desired Interface

后续应将 `solution_summary()` 收敛或替换为语义更窄的接口，例如：

```python
case.solution_metrics(solution, **build_kwargs) -> dict[str, Any]
```

该接口只返回运行正确性和结果审计需要的领域事实。允许字段示例：

- `objective`：用领域 evaluator 复算后的目标值，或从 solution 读取的标准目标值。
- `raw_objective`：不可行解仍需要审计时的原始目标值。
- `reference_objective`：当 case 从原始解文件读取到更精确 reference 时可覆盖 case metadata。
- `decoded_solution`：结构化、可审计的领域解，例如完整 tour、assignment、operation starts 或 activity starts。
- `model_style`：当一次运行的建模变体由 CLI 参数决定，且不同于 case 静态 `modeling_notes` 时可返回。
- `metadata`：少量领域诊断事实；不要把 dashboard 展示字段放入 metadata。

不应由 case 返回的字段：

- solver 通用字段：`solver_name`、`status`、`feasible`、通用 `metadata` 抽取。
- row 派生字段：`gap_abs`、`gap_rel`、`strategy_profile`、`time_to_best_seconds`。
- 展示截断字段：`sequence_head`、`machine_order_head`、`activity_start_head`。
- 纯展示标签或分类：`edge_weight_type` 等仅用于 dashboard 文案或表格列的字段。
- 可由 case metadata 或 family registry 稳定推导的重复字段：静态 `dimension`、默认 `model_style` 等。

## Migration Plan

### Phase 1: Narrow Existing Usage

在不改外部 row contract 的前提下，先减少 `solution_summary()` 的职责：

1. 在 `run.py` 中统一读取 solution 的通用字段。
2. 保留 `solution_summary()` 作为兼容入口，但只把它的返回值视为 case metrics。
3. 将 `sequence_head`、`machine_order_head` 等截断展示字段迁到 `presentation.common.normalize_result_row()` 或发布/报告阶段生成。
4. 对 dashboard 仍依赖的历史字段保持兼容：如果旧 run summary 已经包含字段，presentation 可以继续读取；新 case 不再手工维护。

### Phase 2: Rename Contract

完成兼容收敛后，将接口改名：

```text
solution_summary() -> solution_metrics()
```

迁移规则：

- `BenchmarkCase.solution_metrics()` 提供默认实现，只返回空 dict 或只返回必要领域 objective override。
- `run.py` 负责构造标准 solver summary，再与 case metrics 合并。
- 如果 case metrics 和 runner 标准字段同名，必须显式列出允许覆盖的字段。建议只允许 `objective`、`raw_objective`、`reference_objective`、`model_style`。
- 文档和示例不再鼓励在 case 里写 dashboard-facing `*_head` 字段。

### Phase 3: Presentation Derivations

将展示字段集中在 presentation 层：

- 从 `decoded_solution` 生成 `sequence_head`、`machine_order_head` 等短摘要。
- 从 `case.size`、`case.family`、`case.modeling_notes` 或 row 的标准字段生成 dashboard labels。
- 在 dashboard publish adapter 中决定哪些派生字段进入长期 run summary，哪些只用于临时 run workspace 报告。

## Design Rules

- case 不依赖 presentation schema。
- presentation 不读取 case 私有 build context、node id 或实例对象。
- runner 与 case 之间不传递 benchmark 私有 wrapper 类型。
- 领域 objective 可以在 case 层复算，因为它属于 benchmark correctness，不属于 presentation。
- 展示截断不是 correctness；即使 dashboard 暂时需要，也应由 presentation 从结构化领域解派生。
- 历史 run summary 不重写。兼容逻辑只能在读取和发布新结果时处理。

## Acceptance Criteria

- 新增 case 不需要实现 `solution_summary()` 也能输出 solver 通用字段。
- 实现领域解码的 case 只返回 objective、raw objective、reference override、decoded solution 和必要诊断。
- `rg -n "sequence_head|machine_order_head|activity_start_head" cases` 不再出现新增实现。
- `run.py` 对 solver 通用字段有单一读取路径。
- `presentation/` 对展示字段有单一派生路径。
- 现有 `results.jsonl`、dashboard run summary、index 和 aggregates contract 保持兼容。
