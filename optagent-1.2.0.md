# OptAgent 1.2.0 公共接口速查

本文档基于当前工作区 `.venv312` 中安装的 `optagent 1.2.0` 通过运行时 introspection 整理。`ModelBuilder` 的建模方法通常返回 `Expr[...]`，即内部模型图节点的表达式句柄；变量创建方法会在模型图中注册变量节点。

## 目录

- [常量 / 变量](#常量--变量)
- [目标 / 约束](#目标--约束)
- [表达式算子](#表达式算子)
- [集合 / 序列](#集合--序列)
- [interval / 调度](#interval--调度)
- [其他约束 / 查表 / 外部函数](#其他约束--查表--外部函数)
- [输出模型](#输出模型)
- [求解接口](#求解接口)
- [策略配置](#策略配置)
- [结果对象](#结果对象)
- [最小示例](#最小示例)
- [其他公共对象](#其他公共对象)
- [1.2.0 重要变化](#120-重要变化)

## 常量 / 变量

### ModelBuilder

```python
ModelBuilder(
    *,
    metadata: dict[str, Any] | None = None,
) -> None
```

参数：
- `metadata`：模型级元数据，如 case 名称、来源、模型风格等。

功能：创建建模器，用于添加变量、表达式、约束和目标。

### const

```python
const(
    value: bool | int | float | list[int] | dict[str, int],
) -> Expr[Any]
```

参数：
- `value`：常量值；`list[int]` 常用于列表常量，`dict[str, int]` 常用于 interval 常量。

功能：创建常量表达式节点。

### bool_var

```python
bool_var(
    default: bool = False,
    *,
    name: str | None = None,
) -> Expr[bool]
```

参数：
- `default`：默认布尔值。
- `name`：变量名称，用于诊断、结果识别和外部回调。

功能：创建布尔决策变量。

### int_var

```python
int_var(
    default: int = 0,
    *,
    lb: int | None = None,
    ub: int | None = None,
    name: str | None = None,
) -> Expr[int]
```

参数：
- `default`：默认整数值。
- `lb`：下界；`None` 表示不显式设置。
- `ub`：上界；`None` 表示不显式设置。
- `name`：变量名称。

功能：创建整数决策变量。

### float_var

```python
float_var(
    default: float = 0.0,
    *,
    lb: float | None = None,
    ub: float | None = None,
    name: str | None = None,
) -> Expr[float]
```

参数：
- `default`：默认浮点值。
- `lb`：下界。
- `ub`：上界。
- `name`：变量名称。

功能：创建浮点决策变量。

### set_var

```python
set_var(
    size: int,
    *,
    default: list[int] | set[int] | None = None,
    name: str | None = None,
) -> Expr[list[int]]
```

参数：
- `size`：集合宇宙大小，元素通常为 `0..size-1`。
- `default`：默认选中元素；`None` 表示空集合。
- `name`：变量名称。

功能：创建整数集合变量。

### sequence_var

```python
sequence_var(
    size: int,
    *,
    default: list[int] | None = None,
    name: str | None = None,
) -> Expr[list[int]]
```

参数：
- `size`：序列元素数量，通常表示排列 `0..size-1`。
- `default`：默认序列；`None` 表示 `[0, 1, ..., size-1]`。
- `name`：变量名称。

功能：创建排列/序列变量，适合路径、排序、机器队列等建模。

### interval_var

~~~python
interval_var(
    *,
    start: int = 0,
    length: int = 0,
    lb_start: int | None = None,
    ub_start: int | None = None,
    lb_length: int | None = 0,
    ub_length: int | None = None,
    name: str | None = None,
    scheduling_role: str = "processing",
) -> Expr[dict[str, int]]
~~~

功能：创建必选 interval 变量。interval 具有 start/end/length 结构，scheduling_role 标记调度角色。
### optional_interval_var

~~~python
optional_interval_var(
    *,
    presence: Expr | bool,
    start: int = 0,
    length: int = 0,
    lb_start: int | None = None,
    ub_start: int | None = None,
    lb_length: int | None = 0,
    ub_length: int | None = None,
    name: str | None = None,
    scheduling_role: str = "processing",
) -> Expr[dict[str, int]]
~~~

功能：创建可选 interval 变量。presence 控制是否参与调度；scheduling_role 标记调度角色。
## 目标 / 约束

### minimize / maximize / constraint

```python
minimize(
    expr: Expr | Any,
    *,
    name: str | None = None,
) -> Expr[Any]

maximize(
    expr: Expr | Any,
    *,
    name: str | None = None,
) -> Expr[Any]

constraint(
    expr: Expr | Any,
    *,
    name: str | None = None,
) -> Expr[bool]
```

参数：
- `expr`：目标或约束表达式；约束中非零/真表示满足。
- `name`：目标或约束名称。

功能：添加目标或约束节点。

### exactly_one / at_most_one / at_least_one / alternative

```python
exactly_one(
    *bool_exprs: Expr | Any,
) -> Expr[bool]

at_most_one(
    *bool_exprs: Expr | Any,
) -> Expr[bool]

at_least_one(
    *bool_exprs: Expr | Any,
) -> Expr[bool]

alternative(
    *presence_exprs: Expr | Any,
) -> Expr[bool]

add_alternative(
    *presence_exprs: Expr | Any,
    name: str | None = None,
) -> Expr[bool]
```

参数：
- `bool_exprs` / `presence_exprs`：布尔变量或布尔表达式。
- `name`：`add_alternative` 的约束名称。

功能：表达布尔选择约束。`exactly_one`/`alternative` 表示恰好一个为真，适合机器选择、模式选择等；`add_alternative` 会直接把 alternative 约束加入模型。

## 表达式算子

### 数值 / 逻辑算子

```python
sum(*exprs: Expr | Any) -> Expr[Any]
min(*exprs: Expr | Any) -> Expr[Any]
max(*exprs: Expr | Any) -> Expr[Any]
abs(expr: Expr | Any) -> Expr[Any]
and_(lhs: Expr | Any, rhs: Expr | Any) -> Expr[Any]
or_(lhs: Expr | Any, rhs: Expr | Any) -> Expr[Any]
not_(expr: Expr | Any) -> Expr[Any]
iif(cond: Expr | Any, when_true: Expr | Any, when_false: Expr | Any) -> Expr[Any]
```

参数：
- `exprs`：一个或多个表达式或普通 Python 值。
- `lhs` / `rhs`：左右逻辑表达式。
- `cond`：条件表达式。
- `when_true` / `when_false`：条件分支值。

功能：构造聚合、数值、逻辑和条件表达式。

### Expr 运算符重载

```python
x + y
x - y
x * y
x / y
x // y
x % y
-x
x < y
x <= y
x > y
x >= y
x == y
x != y
```

功能：`Expr` 支持常见算术和比较运算。比较结果仍是模型表达式，不是立即求值的 Python 布尔值。

## 集合 / 序列

### set_len / set_contains / sequence_contains

```python
set_len(set_expr: Expr | Any) -> Expr[Any]
set_contains(set_expr: Expr | Any, value_expr: Expr | Any) -> Expr[Any]
sequence_contains(sequence_expr: Expr | Any, value_expr: Expr | Any) -> Expr[Any]
```

参数：
- `set_expr`：集合变量或集合表达式。
- `sequence_expr`：序列变量或序列表达式。
- `value_expr`：待判断元素。

功能：读取集合大小，或判断集合/序列是否包含某个元素。

### sequence_transition_sum

```python
sequence_transition_sum(
    sequence: Expr | Any,
    graph: TransitionGraph | list[list[int | float]] | dict[str, Any] | Any,
    *,
    include_return_edge: bool = False,
    cost_semantics: str = "penalty",
    sparse_edge_semantics: str = "default_cost",
    default_edge_cost: int | float | None = None,
) -> Expr[Any]
```

参数：
- `sequence`：序列变量。
- `graph`：转移成本图，可为 `TransitionGraph`、方阵、稀疏图字典等。
- `include_return_edge`：是否计算末尾回到开头的边。
- `cost_semantics`：成本语义，常用 `"penalty"`。
- `sparse_edge_semantics`：稀疏图缺失边策略。
- `default_edge_cost`：缺失边默认成本。

功能：按序列累计转移成本，常用于 TSP、路径、排序惩罚等目标。

### sequence_view

~~~python
sequence_view(
    sequence: Expr | Any,
    presences: list[Expr | bool],
    *,
    item_ids: list[int],
    name: str | None = None,
) -> Expr[list[int]]
~~~

功能：按 presence 从基础序列筛选元素并保持相对顺序，得到派生子序列。presences 与 item_ids 对齐，item_ids 必须唯一。

### sequence_successor

~~~python
sequence_successor(
    sequence: Expr | Any,
    *,
    before_item_id: int,
    after_item_id: int,
) -> Expr[bool]
~~~

功能：判断两个元素是否在序列中直接相邻且顺序固定。

### sequence_transition

~~~python
sequence_transition(
    sequence: Expr | Any,
    graph: list[list[int | float]] | dict[str, Any],
    *,
    item_types: list[int],
    start_type: int | None = None,
    valid: bool = False,
    sparse_edge_semantics: str = "default_cost",
    default_edge_cost: int | float | None = 0,
    name: str | None = None,
) -> Expr[Any]
~~~

功能：按序列转移图计算成本，或在 valid=True 时表达转移合法性。

### sequence_dimension

~~~python
sequence_dimension(
    sequence: Expr | Any,
    *,
    initial_value: Expr | int | float,
    contributions: list[Expr | int | float],
    item_types: list[int],
    reset_item_ids: list[int],
    reset_type_edges: list[tuple[int, int]],
    query_item_id: int,
    query: str,
    lower_bound: float | None = None,
    upper_bound: float | None = None,
    name: str | None = None,
) -> Expr[Any]
~~~

功能：沿序列累计贡献并按 reset 元素或类型重置，适合分段负载和累计量。

### sequence_setup

~~~python
sequence_setup(
    sequence: Expr | Any,
    intervals: list[Expr | Any],
    graph: list[list[int | float]] | dict[str, Any],
    *,
    item_types: list[int],
    start_type: int | None = None,
    sparse_edge_semantics: str = "default_cost",
    default_edge_cost: int | float | None = 0,
    name: str | None = None,
) -> Expr[bool]
~~~

功能：根据序列转移图和 interval 顺序表达 setup/切换约束。

### TransitionGraph

```python
TransitionGraph(size: int) -> None
TransitionGraph.from_matrix(matrix: list[list[int | float]]) -> TransitionGraph
edge(from_node: int, to_node: int, *, cost: int | float) -> TransitionGraph
default_cost(cost: int | float) -> TransitionGraph
implicit_zero() -> TransitionGraph
forbid_missing() -> TransitionGraph
```

参数：
- `size`：节点数，节点编号为 `0..size-1`。
- `matrix`：方阵成本。
- `from_node` / `to_node`：有向边端点。
- `cost`：边成本或默认成本。

功能：构造序列转移成本图，可传给 `sequence_transition_sum`。

## interval / 调度

### interval_start / interval_end / interval_length / interval_presence

```python
interval_start(interval_expr: Expr | Any) -> Expr[Any]
interval_end(interval_expr: Expr | Any) -> Expr[Any]
interval_length(interval_expr: Expr | Any) -> Expr[Any]
interval_presence(interval_expr: Expr | Any) -> Expr[bool]
```

参数：
- `interval_expr`：必选或可选 interval 表达式。

功能：读取 interval 的开始、结束、持续时间和 presence。必选 interval 的 presence 恒为真。

### precedence

```python
precedence(
    before_interval: Expr | Any,
    after_interval: Expr | Any,
    *,
    lag: Expr | int = 0,
) -> Expr[Any]
```

参数：
- `before_interval`：前置 interval。
- `after_interval`：后置 interval。
- `lag`：最小间隔。

功能：表达 `end(before) + lag <= start(after)`。

### no_overlap

```python
no_overlap(
    sequence_expr: Expr | Any,
    *interval_exprs: Expr | Any,
) -> Expr[Any]
```

参数：
- `sequence_expr`：决定 interval 排序的序列变量。
- `interval_exprs`：同一资源上不能重叠的 interval 列表。

功能：表达机器/资源上的互斥加工约束。对 optional interval，求解器应根据 presence 判断是否参与。

### cumulative

```python
cumulative(
    intervals: list[Expr | Any],
    demands: list[Expr | Any],
    capacity: Expr | Any,
) -> Expr[Any]
```

参数：
- `intervals`：占用资源的 interval 列表。
- `demands`：每个 interval 的资源需求。
- `capacity`：资源容量。

功能：表达累计资源容量约束。

### selected_start / selected_end / selected_duration

```python
selected_start(
    intervals: list[Expr | Any] | tuple[Expr | Any, ...],
    presences: list[Expr | Any] | tuple[Expr | Any, ...],
) -> Expr[Any]

selected_end(
    intervals: list[Expr | Any] | tuple[Expr | Any, ...],
    presences: list[Expr | Any] | tuple[Expr | Any, ...],
) -> Expr[Any]

selected_duration(
    intervals: list[Expr | Any] | tuple[Expr | Any, ...],
    presences: list[Expr | Any] | tuple[Expr | Any, ...],
) -> Expr[Any]
```

参数：
- `intervals`：候选 optional interval 列表。
- `presences`：与 `intervals` 对齐的 presence 表达式列表。

功能：返回被选中 interval 的 start/end/duration。调用者需要自行用 `exactly_one` 或 `alternative` 保证恰好一个 presence 为真。

## 其他约束 / 查表 / 外部函数

### all_different

```python
all_different(
    *exprs: Expr | Any,
) -> Expr[Any]
```

参数：
- `exprs`：需要两两不同的表达式。

功能：全局 all-different 约束表达式。

### element

```python
element(
    array_values: list[int | float],
    index_expr: Expr | Any,
) -> Expr[Any]
```

参数：
- `array_values`：固定数组。
- `index_expr`：索引表达式。

功能：表达 `array_values[index_expr]`。

### table

```python
table(
    exprs: list[Expr | Any],
    allowed_tuples: list[list[int]],
) -> Expr[Any]
```

参数：
- `exprs`：组成元组的表达式列表。
- `allowed_tuples`：允许的取值元组列表。

功能：表约束，要求表达式元组属于允许集合。

### external_call

```python
external_call(
    fn: Callable[[ExternalCallbackContext], Any],
    name: str | None = None,
    value_kind: ValueKind = ValueKind.SCALAR,
    timeout_ms: int | None = None,
    pure: bool = True,
    deterministic: bool = True,
    cacheable: bool | None = None,
    batch_fn: Callable[[list[list[Any]]], list[Any]] | None = None,
    batch_safe: bool | None = None,
    concurrency_mode: str | ExternalConcurrencyMode = "shared_serial",
    worker_factory: Callable[[], Callable[[ExternalCallbackContext], Any]] | None = None,
    error_policy: str = "fail",
    depends_on: tuple[Any, ...] | list[Any] = (),
) -> Expr[Any]
```

参数：
- `fn`：外部 Python 回调，签名通常为 `fn(ctx) -> value`。
- `name`：回调名称。
- `value_kind`：返回值类型语义。
- `timeout_ms`：超时时间。
- `pure`：是否无副作用。
- `deterministic`：相同输入是否确定返回相同输出。
- `cacheable`：是否可缓存。
- `batch_fn`：批量回调。
- `batch_safe`：是否可批量安全调用。
- concurrency_mode：并发模式，当前默认值为 shared_serial。
- worker_factory：创建隔离 worker 回调的工厂。
- `error_policy`：错误策略，常用 `"fail"`。
- `depends_on`：显式依赖变量/表达式。

功能：把 Python 函数注册为模型中的外部评价节点，适合黑盒目标、复杂约束或暂时难以原生建模的逻辑。

### ExternalCallbackContext

```python
value(ref: Any) -> Any
depends_on(*refs: Any) -> None
close() -> None
```

功能：外部回调上下文。`value(ref)` 读取变量或表达式当前值；`depends_on` 声明额外依赖。

## 输出模型

### to_program_spec

```python
to_program_spec() -> ProgramSpec
```

功能：把模型转换为可序列化的 `ProgramSpec`，适合检查、导出 JSON 或跨语言传递。外部函数 callable 不会被序列化。

### freeze

```python
freeze() -> ExecutableProgram
```

功能：冻结模型，返回可执行程序。冻结后模型图不可变；返回对象保留外部函数注册表，可直接传给 `solve`。

### ProgramSpec JSON

```python
programspec_to_json(
    spec: ProgramSpec,
    path: str | Path | None = None,
) -> str

programspec_from_json(
    payload: str | bytes | Path,
) -> ProgramSpec

executable_from_json(
    payload: str | bytes | Path,
    *,
    external_registry: dict[str, Callable[..., Any]] | None = None,
) -> Any
```

参数：
- `spec`：待序列化的程序规格。
- `path`：可选输出路径。
- `payload`：JSON 字符串、bytes 或 JSON 文件路径。
- `external_registry`：反序列化 executable 时用于恢复外部函数的注册表。

功能：序列化/反序列化模型 IR。

## 求解接口

### solve

~~~python
solve(
    model_or_program: Any,
    *,
    strategy: StrategyConfig | None = None,
    max_iterations: int | None = None,
    time_limit_s: float = 30.0,
    seed: int = 0,
    threads: int | None = None,
    log_level: str = "on",
    trace_output: str | None = None,
    trace_limit: int | None = None,
    observation_times_s: Sequence[float] | None = None,
    reproduction_path: str | Path | None = None,
) -> UnifiedSolution
~~~

参数：
- model_or_program：ModelBuilder、ExecutableProgram、ProgramSpec，或带 to_program_spec() 的对象。
- strategy：StrategyConfig 对象；当前顶层策略注册表只包含 GA。
- max_iterations：最大迭代次数。
- time_limit_s：时间限制秒数。
- seed：随机种子。
- threads：线程数。
- log_level：日志等级，默认 "on"。
- trace_output / trace_limit：trace 输出模式和条数。
- observation_times_s：采集解观察快照的时间点。
- reproduction_path：保存可复现实验捕获文件的路径。

功能：调用原生 C++ search kernel 进行启发式/元启发式求解，返回 UnifiedSolution。
### solve_cpsat

```python
solve_cpsat(
    model_or_program: Any,
    *,
    config: CpSatConfig | None = None,
    warm_start: dict[int, object] | None = None,
    time_limit_s: float | None = None,
    time_limit_seconds: float | None = None,
    workers: int | None = None,
    random_seed: int | None = None,
    relative_gap_limit: float | None = None,
    absolute_gap_limit: float | None = None,
    log_search_progress: bool | None = None,
    log_to_stdout: bool | None = None,
    profile_solve: bool | None = None,
    enable_solution_callback: bool | None = None,
    solution_event_limit: int | None = None,
    parameters: dict[str, object] | None = None,
    reproduction_path: str | Path | None = None,
    **cp_sat_parameters: object,
) -> UnifiedSolution
```

参数：
- `model_or_program`：待求解模型。
- `config`：`CpSatConfig` 配置对象。
- `warm_start`：初始解，格式为 `{variable_node_id: value}`。
- `time_limit_s` / `time_limit_seconds`：时间限制。
- `workers`：CP-SAT worker 数。
- `random_seed`：随机种子。
- `relative_gap_limit`：相对 gap 停止阈值。
- `absolute_gap_limit`：绝对 gap 停止阈值。
- `log_search_progress`：是否启用 CP-SAT 搜索日志。
- `log_to_stdout`：是否输出到 stdout。
- `profile_solve`：是否记录求解 profile。
- `enable_solution_callback`：是否启用 solution callback。
- `solution_event_limit`：callback 事件上限。
- `parameters`：额外 CP-SAT 参数字典。
- `cp_sat_parameters`：额外 CP-SAT 参数关键字。

功能：绕过原生启发式 kernel，直接调用 OR-Tools CP-SAT 求解。不要同时传 `config` 和一组散装 CP-SAT 参数。

### solve_milp / solve_optx

~~~python
solve_milp(
    model_or_program: Any,
    *,
    config: MilpConfig | None = None,
    warm_start: dict[int, object] | None = None,
    reproduction_path: str | Path | None = None,
) -> UnifiedSolution

solve_optx(
    model_or_program: Any,
    *,
    config: OptxConfig | None = None,
    warm_start: dict[int, object] | None = None,
    reproduction_path: str | Path | None = None,
) -> UnifiedSolution
~~~

参数：
- model_or_program：待求解模型。
- config：MILP/OptX 配置对象。
- warm_start：初始变量赋值，格式为 {variable_node_id: value}。
- reproduction_path：可选的复现实验捕获路径。

功能：调用 MILP/OptX 精确后端，适合可线性化模型。
### 策略工具函数

~~~python
default_strategy_config() -> StrategyConfig
normalize_strategy_config(strategy: StrategyConfig) -> StrategyConfig
pareto_front(solutions: list[UnifiedSolution]) -> list[UnifiedSolution]
~~~

功能：获取默认策略配置、标准化 StrategyConfig、计算 Pareto front。当前 normalize_strategy_config 不接收策略字符串。
## 策略配置

### StrategyConfig

```python
StrategyConfig() -> None
```

参数：无公开初始化参数。

功能：策略配置基类。通常不直接实例化；当前顶层默认策略为 `GaConfig`，精确后端分别使用 `CpSatConfig`、`MilpConfig`、`OptxConfig`。

### GaConfig

~~~python
GaConfig(
    max_iterations: int | None = None,
    unimproved_iteration_limit: int | None = None,
    population_size: int = 8,
    crossover_rate: float = 0.35,
) -> None
~~~

功能：遗传算法配置。当前 1.2.0 构造签名只包含以上四个字段。
### AlnsConfig

AlnsConfig 仍可从 optagent.strategy 模块看到，但当前顶层 optagent 未导出它，且 STRATEGY_CONFIGS 当前只注册 ga。因此不应把 ALNS 记为当前默认公共策略。
### CpSatConfig

```python
CpSatConfig(
    time_limit_s: float | None = None,
    workers: int | None = None,
    random_seed: int | None = None,
    relative_gap_limit: float | None = None,
    absolute_gap_limit: float | None = None,
    log_search_progress: bool = False,
    log_to_stdout: bool | None = None,
    profile_solve: bool = False,
    enable_solution_callback: bool = False,
    solution_event_limit: int = 20,
) -> None
```

功能：OR-Tools CP-SAT 配置。

### MilpConfig / OptxConfig

```python
MilpConfig(
    time_limit_s: float | None = None,
    threads: int | None = None,
    mip_rel_gap: float | None = None,
    backend: str | None = None,
) -> None

OptxConfig(
    time_limit_s: float | None = None,
    mip_rel_gap: float | None = None,
    threads: int | None = None,
) -> None
```

功能：MILP/OptX 精确后端配置。

## 结果对象

### UnifiedSolution

~~~python
UnifiedSolution(
    solver_name: str,
    status: SolutionStatus,
    variable_values: dict[int, Any],
    objective_values: dict[int, Any],
    constraint_values: dict[int, Any],
    feasible: bool,
    dag_recheck_passed: bool,
    result: SolveResult = <factory>,
    summary: SolveSummary = <factory>,
    diagnostics: dict[str, Any] = <factory>,
    telemetry: dict[str, Any] = <factory>,
    observations: list[SolveObservation] = <factory>,
    solution_snapshots: dict[str, IncumbentSnapshot] = <factory>,
) -> None
~~~

常用属性：
- solver_name、status、variable_values、objective_values、constraint_values。
- objective_value：首个目标值的便捷属性。
- feasible：是否可行。
- diagnostics、telemetry：诊断和遥测信息。
- observations：按 observation_times_s 采集的解观察结果。
- solution_snapshots：按名称记录的 incumbent 快照。

### SolutionStatus

常见状态：
- `OPTIMAL`：已证明最优。
- `FEASIBLE`：找到可行解但未证明最优。
- `INFEASIBLE`：不可行或未找到可行解。
- `FAILED`：求解失败。
- `FALLBACK`：从 fallback 路径返回。

### MultiSolutionArchive

```python
MultiSolutionArchive(
    top_k: int = 1,
    solutions: list[UnifiedSolution] = <factory>,
) -> None

add(solution: UnifiedSolution) -> None
to_dict() -> dict[str, Any]
```

功能：保存多个解并导出为字典。

## 最小示例

### GA

```python
from optagent import ModelBuilder, GaConfig, solve

builder = ModelBuilder(metadata={"name": "tiny"})
x = builder.int_var(default=0, lb=0, ub=10, name="x")
y = builder.int_var(default=0, lb=0, ub=10, name="y")
builder.constraint(x + y >= 5, name="demand")
builder.minimize(x + 2 * y, name="cost")

solution = solve(
    builder,
    strategy=GaConfig(max_iterations=20, population_size=8),
    time_limit_s=2.0,
    seed=11,
)
print(solution.feasible, solution.objective_value)
```

### CP-SAT

```python
from optagent import ModelBuilder, CpSatConfig, solve_cpsat

builder = ModelBuilder()
x = builder.int_var(default=0, lb=0, ub=10, name="x")
y = builder.int_var(default=0, lb=0, ub=10, name="y")
builder.constraint(x + y >= 5)
builder.minimize(x + 2 * y)

solution = solve_cpsat(
    builder,
    config=CpSatConfig(time_limit_s=5.0, workers=1, random_seed=11),
)
print(solution.status, solution.objective_value)
```

### FJSP optional interval 骨架

```python
from optagent import ModelBuilder

builder = ModelBuilder(metadata={"model_style": "optional_interval_fjsp"})
horizon = 100

p0 = builder.bool_var(default=True, name="choose_op0_m0")
p1 = builder.bool_var(default=False, name="choose_op0_m1")

iv0 = builder.optional_interval_var(
    presence=p0,
    start=0,
    length=5,
    lb_start=0,
    ub_start=horizon,
    lb_length=5,
    ub_length=5,
    name="op0_m0",
)
iv1 = builder.optional_interval_var(
    presence=p1,
    start=0,
    length=7,
    lb_start=0,
    ub_start=horizon,
    lb_length=7,
    ub_length=7,
    name="op0_m1",
)

builder.constraint(builder.exactly_one(p0, p1), name="op0_choose_one")
selected_end = builder.selected_end([iv0, iv1], [p0, p1])
builder.minimize(selected_end, name="makespan")
```

## 其他公共对象

### SchedulingModel

```python
SchedulingModel(
    builder: ModelBuilder,
    *,
    horizon: int,
) -> None
```

参数：
- `builder`：底层 `ModelBuilder`，用于承载最终生成的变量、约束和目标。
- `horizon`：调度时间范围上界，用于创建任务 interval 和资源约束。

常用方法：

```python
task(
    name: str,
    *,
    attrs: dict[str, Any] | None = None,
    tags: Iterable[str] | None = None,
) -> Task

resource(
    name: str | Resource,
    *,
    kind: str = "unary",
    capacity: int | Expr[int] | None = None,
    attrs: dict[str, Any] | None = None,
) -> Resource

unary_resource(
    name: str,
    *,
    attrs: dict[str, Any] | None = None,
) -> Resource

cumulative_resource(
    name: str,
    *,
    capacity: int | Expr[int],
    attrs: dict[str, Any] | None = None,
) -> Resource

precedence(
    before: Task | Alternative,
    after: Task | Alternative,
    *,
    lag: Expr | int = 0,
) -> list[Expr[Any]]

chain(
    tasks: Iterable[Task],
    *,
    lag: Expr | int = 0,
) -> list[Expr[Any]]

exactly_one_alternative(
    task: Task,
    *,
    name: str | None = None,
) -> Expr[bool]

makespan(
    tasks: Iterable[Task] | None = None,
) -> Expr[Any]

resource_load(
    resource: str | Resource,
) -> Expr[Any]

load_balance(
    resources: Iterable[str | Resource] | None = None,
) -> Expr[Any]

total_earliness(
    *,
    tasks: Iterable[Task] | None = None,
    due_attr: str = "due",
) -> Expr[Any]

total_tardiness(
    *,
    tasks: Iterable[Task] | None = None,
    due_attr: str = "due",
) -> Expr[Any]

transition_cost(*args: Any, **kwargs: Any) -> Expr[Any]

compile() -> ModelBuilder
apply() -> ModelBuilder
diagnostics() -> dict[str, Any]
```

参数：
- `name`：任务或资源名称。
- `attrs`：附加属性字典，如加工时间、到期时间、资源容量等领域信息。
- `tags`：任务标签，用于分类或后续筛选。
- `kind`：资源类型，常见为 `"unary"`。
- `capacity`：资源容量，累计资源必须提供。
- `before` / `after`：前后任务或备选加工方案。
- `lag`：前后任务之间的最小间隔。
- `task`：包含多个 alternative 的任务。
- `tasks`：参与统计或目标表达式的任务集合；为 `None` 时通常表示全部任务。
- `resource` / `resources`：参与负载统计的资源。
- `due_attr`：任务属性中表示 due date 的字段名。
- `*args` / `**kwargs`：当前公开但未稳定细化的扩展参数。

功能：调度问题的领域建模辅助层。它在 `ModelBuilder` 之上组织任务、资源、工序链、备选加工、makespan、资源负载和提前/拖期目标，最后通过 `compile()` 或 `apply()` 写回底层模型。`batch`、`calendar`、`lexicographic`、`optional_group`、`setup_time`、`span`、`split_operation`、`synchronize` 等方法当前公开签名为通用占位参数，使用前应结合版本实现确认语义。

### DiagnosticPayload / 异常类

```python
DiagnosticPayload(
    message: str,
    backend: str,
    phase: str,
    error_type: str,
    node_id: int | None = None,
    node_kind: str | None = None,
    move: str | None = None,
    changed_nodes: list[int] = [],
    roots: list[int] = [],
    phase_objectives: list[int] = [],
    trace_tail: list[dict[str, Any]] = [],
) -> None
```

参数：
- `message`：诊断消息。
- `backend`：产生诊断的后端名称。
- `phase`：失败或诊断发生的阶段。
- `error_type`：错误类型标识。
- `node_id`：相关模型节点 id。
- `node_kind`：相关模型节点类型。
- `move`：相关搜索 move 名称。
- `changed_nodes`：本次变化涉及的节点 id。
- `roots`：相关根节点 id。
- `phase_objectives`：相关阶段目标节点 id。
- `trace_tail`：末尾 trace 片段。

功能：标准化求解诊断信息，通常出现在异常、`UnifiedSolution.diagnostics` 或调试输出中。

公开异常类：
- `KernelUnsupportedError`：当前后端不支持模型中的某类节点或特性。
- `SchedulingUnsupportedFeatureError`：调度便捷层遇到尚不支持的调度特性。
- `SolverDiagnosticError`：带诊断信息的求解错误。
- `SolverTypeError`：模型或参数类型错误。
- `SolverValueError`：模型或参数取值错误。
- `ExternalEvaluationError`：外部函数评价失败。
- `ExternalTimeoutError`：外部函数评价超时。

## 1.2.0 重要变化

- 当前 wheel 版本为 OptAgent 1.2.0，不再按 1.2.0rc1 记录。
- solve 新增 observation_times_s、reproduction_path，删除旧版 diagnostics、diagnostics_path。
- solve_cpsat、solve_milp、solve_optx 支持 reproduction_path。
- interval_var 和 optional_interval_var 新增 scheduling_role。
- external_call 的并发参数改为 concurrency_mode、worker_factory。
- 新增 sequence_view、sequence_successor、sequence_transition、sequence_dimension、sequence_setup。
- sequence_transition_sum 支持 TransitionGraph、稀疏图语义和 cost_semantics。
- 当前顶层 STRATEGY_CONFIGS 只注册 ga；AlnsConfig 不再是顶层默认公共策略配置。
- GaConfig 当前签名收缩为 max_iterations、unimproved_iteration_limit、population_size、crossover_rate。
- UnifiedSolution 新增 observations、solution_snapshots。
- normalize_strategy_config 当前接收 StrategyConfig 对象，不应按旧文档传入字符串。
