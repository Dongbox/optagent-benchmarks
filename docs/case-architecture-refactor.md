# Case Architecture Refactor Phased Development Plan

> Superseded note: the target interface in this historical plan has been replaced by
> [BenchmarkCase ModelBuilder Interface Roadmap](benchmark-case-modelbuilder-interface-requirements.md).
> New development should use `BenchmarkCase.build_model() -> ModelBuilder`, root `run.py`
> strategy orchestration, and `solution_summary()` instead of case-level `load_instance()`,
> `StrategyDeclaration`, or series-level `solve_case()`.

本文档定义 benchmark case 架构重构的分阶段开发计划。目标是让新增实例的开发者只需要关注问题描述、建模函数、默认策略声明和实例内 `solve_case()`，同时把通用本地测试入口放在 `benchmarks/run.py`，特定评测场景输出和 dashboard-facing 工具统一放在 `presentation/`。

## Final Shape

目标源码结构：

```text
run.py
cases/
  base.py
  common.py
  jsplib/
    scheduling/
      jobshop/
        __init__.py
        raw/
          data.py
        abz.py
        ft.py
        la.py
  tsplib/
    routing/
      tsp/
        __init__.py
        raw/
          data.py
        berlin.py
        kroa.py
  qaplib/
    assignment/
      quadratic_assignment/
        __init__.py
        raw/
          data.py
        nug.py
        chr.py
presentation/
  suite.py
  compare.py
  dashboard.py
  publish_dashboard_results.py
  generate_dashboard_data.py
```

目录语义：

- `cases/<数据来源>/<问题类型>/<实例类型>/<实例>.py` 是实例声明和默认运行的主位置。
- `<问题类型>` 直接使用目录名，例如 `scheduling`、`routing`、`assignment`、`exact`。
- 一个实例文件可以声明同一实例族下多个不同规模 case，例如 `abz.py` 包含 `abz5`、`abz7`。
- `raw/data.py` 只处理公开原始数据解析、下载、缓存路径和原始格式说明。
- 不新增固定 `model.py` 或 `solve.py` 层。建模和默认求解入口优先跟随具体实例模块。
- 允许实例文件之间存在相似甚至重复的建模、预算和求解逻辑；实例单独维护全流程更适合协同开发。
- 只有当重复已经明显阻碍维护时，才抽取语义明确的同目录 helper，例如 `jobshop_modeling.py` 或 `jobshop_solve.py`。
- `benchmarks/run.py` 是本地通用测试入口，集成 case 收集、过滤和单 case 调用能力。
- `presentation/` 承载特定评测场景输出、标准 suite artifact 写入、对比报告、dashboard 发布和静态聚合数据生成。
- 不再保留 `presentation/` 目录。

## Non Goals

- 不修改公开 OptAgent modeling/solve API。
- 不让 benchmark 正确性依赖 private OptAgent source-tree internals。
- 不修改 `docs/result-json-contract.md` 或 `docs/dashboard-data-contract.md` 的核心 schema。
- 不恢复顶层 `loaders/`、`models/`、`catalog/`、`definitions/` 或 `data-cache/` 目录。
- 不把历史 `presentation/results/` 或 `presentation/aggregates/` 作为架构迁移试验对象。

## Core Types

### `BenchmarkCase`

新增 `cases/base.py`，定义 frozen dataclass 形式的 `BenchmarkCase`。后续如有必要可演进为 Protocol 或 ABC。

建议字段：

```python
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
    size: Mapping[str, int | float | str]
    data: Mapping[str, Any]
    reference: Mapping[str, Any]
    problem_description: str
    modeling_notes: Mapping[str, Any] = field(default_factory=dict)
    default_strategies: tuple["StrategyDeclaration", ...]
    case_module: str
```

建议行为：

- `to_row() -> dict[str, Any]`：返回 presentation、根入口和 presentation publication 可消费的兼容 dict。
- `load_instance(**kwargs) -> Any`：默认抛出 `NotImplementedError`，由实例子类或实例模块实现。
- `build_model(instance_data: Any | None = None, **kwargs) -> Any`：默认抛出 `NotImplementedError`。
- `default_strategy_names() -> tuple[str, ...]`：返回默认策略名。
- `strategy_config(name: str) -> Any`：按实例模块固定默认预算和策略声明实例化公开 OptAgent 策略配置。
- `reference_objective() -> float | None`：统一读取 reference objective 或 cost。

设计要求：

- `compare_key` 表达跨策略对比的稳定粒度，通常为 `<source>/<problem_type>/<instance_type>/<instance>`。
- `series_key` 表达趋势序列粒度，通常在 `compare_key` 基础上追加可影响建模结果的模型变体。
- `problem_description` 是必填的人类可读问题描述。
- `modeling_notes` 只记录少量辅助信息，例如 `model_style`、`objective_sense`、`public_api_primitives`。不要要求开发者手工维护完整变量、约束、目标函数清单。
- `BenchmarkCase` 不写文件，不知道 runner 输出目录，不持有私有 OptAgent 对象。

### `StrategyDeclaration`

新增 `StrategyDeclaration`，描述默认测试路径支持的公开 OptAgent 策略类和固定配置。

建议字段：

```python
@dataclass(frozen=True)
class StrategyDeclaration:
    name: str
    config_class: str
    profile: str
    kind: str = "strategy_run"
    config: Mapping[str, Any] = field(default_factory=dict)
    notes: str | None = None
```

设计要求：

- `config_class` 使用公开 OptAgent 策略类名，例如 `GaConfig`、`AlnsConfig`、`LnsConfig`。
- 默认策略预算由具体实例模块固定声明。
- MIPLIB 等 exact baseline 不引入特殊层级；它仍作为同一 case/strategy 层级表达，由策略名称和配置类决定求解方式。
- 根入口和presentation 场景脚本 做对比实验时可以忽略默认策略声明，自行构造策略。

## Series Module Contract

每个 `cases/<source>/<problem_type>/<instance_type>/<series>.py` 应自包含默认全流程。单实例系列仍按系列文件处理，不恢复旧的 per-instance shim。

必须包含：

- readable 常量，例如 `SOURCE`、`PROBLEM_TYPE`、`INSTANCE_TYPE`、`CASE_MODULE`；
- 一个或多个 case 对象，例如 `ABZ5`、`ABZ7`；
- `CASES: tuple[BenchmarkCase, ...]`；
- `PROBLEM_DESCRIPTION` 或每个 case 自己的 `problem_description`；
- 默认策略声明和固定配置；
- `load_instance(instance: str = ..., **kwargs) -> Any`；
- `build_model(instance_data: Any, instance: str = ...) -> Any`；
- `solve_case(instance: str, **kwargs) -> list[dict[str, Any]]`。

不要包含：

- 大型不透明 metadata 字典；
- 需要手工同步代码的完整建模说明；
- 通过 `replace()` 等方式从一个 case 推导未核验或不存在的另一个 case；
- 不属于当前 `CASES` 的公开实例名、默认实例、便捷方法或错误提示；
- 迁移来源系列的兼容别名，例如非 ABZ 模块中的 `solve_abz5()`；
- 对 private OptAgent internals 的依赖。

示例轮廓：

```python
ABZ5 = JobShopCase(
    benchmark_id="jsplib_abz5",
    instance="abz5",
    tier="calibration",
    size={"jobs": 10, "machines": 10, "operations": 100},
    reference={...},
    problem_description=PROBLEM_DESCRIPTION,
    modeling_notes={"model_style": "interval_job_shop"},
    default_strategies=(JOBSHOP_CPSAT, JOBSHOP_GA, JOBSHOP_ALNS),
    case_module=__name__,
)

ABZ7 = JobShopCase(
    benchmark_id="jsplib_abz7",
    instance="abz7",
    tier="full",
    size={"jobs": 20, "machines": 15, "operations": 300},
    reference={...},
    problem_description=PROBLEM_DESCRIPTION,
    modeling_notes={"model_style": "interval_job_shop"},
    default_strategies=(JOBSHOP_CPSAT, JOBSHOP_GA, JOBSHOP_ALNS),
    case_module=__name__,
)

CASES = (ABZ5, ABZ7)
```

`solve_case()` 是 cases 内部默认路径，不是复杂实验 runner。它负责 load、build、按默认策略求解、生成标准 result rows，并在 setup error 或 solver error 时返回 error rows。

`CASE_MODULE` 应使用当前模块名，优先写作 `CASE_MODULE = __name__`。registry 根据每个 case 的 `case_module` 导入系列模块，并把 case 自身的 `instance` 显式传入 `solve_case(instance, ...)`。

## Root Entry And Runners

`benchmarks/run.py` 是通用测试入口，面向开发者日常调试。

职责：

- 列出 case；
- 选择 case；
- 调用实例模块的 `solve_case()`；
- 允许传入自定义策略或策略配置；
- 输出本地测试结果；
- 保持轻量，不承担正式评测场景的矩阵编排和发布职责。

建议 API：

```python
def run_case(
    case: BenchmarkCase | str,
    *,
    strategies: tuple[Any, ...] | None = None,
    allow_download: bool = True,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    ...
```

`presentation/` 不再作为通用运行层。`presentation/` 下新增文件必须对应一个具体目标评测场景。presentation 场景脚本 可以只导入 case 对象和建模函数，然后自定义策略求解。

根入口和presentation 场景脚本 都不应定义公开数据解析、默认 case metadata、默认问题描述、默认建模函数或实例族默认策略配置。

## Phase 0: Baseline Audit

目标：

- 明确当前工作树中已有迁移状态。
- 记录哪些文件是旧结构、过渡结构、目标结构。
- 避免误改 presentation 历史产物。

改动范围：

- 只读检查，不做行为变更。

建议检查：

- `cases/` 下现有实例模块、顶层 family 模块和 raw data 模块。
- `presentation/` 下哪些文件是通用 runner，哪些已经是具体评测场景。
- `cases/registry.py`、`presentation/suite.py` 的调用链。
- `docs/result-json-contract.md` 和 `docs/dashboard-data-contract.md` 对结果字段的要求。

交付物：

- 一份迁移清单，列出每个 family 的当前入口、模型构建位置、默认求解位置、runner 依赖。

验收：

- 清楚标记首个试点 family。
- 确认不会修改 `presentation/results/` 和 `presentation/aggregates/`，除非后续阶段显式要求。

## Phase 1: Base Case API

目标：

- 建立 `BenchmarkCase` 和 `StrategyDeclaration`，为后续实例迁移提供类型边界。
- 保持向后兼容，允许过渡期 dict 与 `BenchmarkCase` 并存。

改动范围：

- 新增 `cases/base.py`。
- 小范围调整 `cases/registry.py` 和可能的 。

交付物：

- `BenchmarkCase` dataclass。
- `StrategyDeclaration` dataclass。
- `BenchmarkCase.to_row()`。
- dict adapter 或兼容读取逻辑。
- `cases.registry.benchmark_cases()` 能返回稳定 case 集合。

验收：

- 现有 dict case 不被破坏。
- `BenchmarkCase.to_row()` 输出包含当前 result row 依赖的基础字段。
- focused import test 能导入 `benchmarks.cases.base` 和 `benchmarks.cases.registry`。

注意事项：

- 不新增 `ModelingDeclaration`。
- 不要求实例维护完整变量、约束、目标函数清单。

## Phase 2: Instance Self-Contained Pilot

目标：

- 选择一个实例族试点，把 case 声明、问题描述、建模、默认策略、默认 `solve_case()` 放进实例模块。
- 推荐试点：`cases/jsplib/scheduling/jobshop/abz.py`。

改动范围：

- `cases/jsplib/scheduling/jobshop/abz.py`。
- `cases/jsplib/scheduling/jobshop/__init__.py`。
- 必要时调整 `cases/jsplib/scheduling/jobshop/raw/data.py`。
- 仅在确有必要时保留语义 helper；不要创建固定 `model.py` 或 `solve.py`。

交付物：

- `ABZ5`、`ABZ7` 等显式 case 对象。
- `CASES`。
- `load_instance()`。
- `build_model()`。
- 默认策略声明和固定预算配置。
- `solve_case()`。

验收：

- `abz.py` 单文件即可看懂该实例族默认全流程。
- 不通过 `replace()` 从一个 case 派生未核验的另一个 case。
- `solve_case("abz5")` 返回标准 row 或 error row。
- 失败路径不会中断整个调用。

注意事项：

- 允许与其他 jobshop 实例重复建模或求解逻辑。
- 先保证实例自包含和协同开发清晰度，再考虑抽 helper。

## Phase 3: Root Development Entry

目标：

- 新增或改造 `benchmarks/run.py`，作为通用 case 调用和自定义策略测试入口。
- 将通用本地测试从 `presentation/` 中剥离。

改动范围：

- `run.py`。
- `cases/registry.py`。
- 需要时调整 package import。

交付物：

- `python -m benchmarks.run --list-cases`。
- `python -m benchmarks.run --case <benchmark_id>`。
- `run_case(case, strategies=..., allow_download=...)` Python API。
- 本地输出 rows，不承担正式 publication。

验收：

- 能列出迁移后的 pilot case。
- 能调用 pilot case 的实例内 `solve_case()`。
- 能传入自定义策略或策略配置做本地测试。
- 输出 row 字段与现有 contract 兼容。

注意事项：

- 根入口保持轻量。
- 不在根入口定义默认 case metadata、问题描述、建模函数或默认策略配置。

## Phase 4: Registry And Existing Runner Boundary

目标：

- 让通用入口、presentation 场景脚本 和 presentation publication 都只依赖 `BenchmarkCase.to_row()` 或实例模块公开入口。
- 将 `presentation/` 中通用 suite 逻辑下沉、迁移或标注为具体评测场景。

改动范围：

- `cases/registry.py`。
- 。
- `presentation/suite.py` 等现有通用 runner。
- README 或开发说明中的运行命令。

交付物：

- `presentation/` 下文件按目标评测场景命名或注释说明。
- 新增 runner 文件必须说明服务的评测场景。
- `presentation/` 不再持有 family 默认预算 dataclass 导入和默认策略配置。

验收：

- `presentation/` 不作为默认新增通用运行层。
- `presentation/` 中具体场景仍可导入模型并自定义策略做对比。
- 现有 dashboard publication 或 result generation 路径不因入口重构而破坏。

注意事项：

- 若现有 `presentation/run.py` 暂时保留，应明确为兼容 shim 或具体 suite 场景入口。
- 不要把 case 默认逻辑留在 presentation 脚本中。

## Phase 5: Family Migration

目标：

- 按 Phase 2 模式迁移其余 family。

候选顺序：

1. JSPLIB jobshop。
2. TSPLIB TSP。
3. QAPLIB quadratic assignment。
4. PSPLIB RCPSP。
5. MIPLIB linear MIP。

每个 family 的改动范围：

- 对应 `cases/<source>/<problem_type>/<instance_type>/<instance>.py`。
- 对应 `__init__.py` 的 `CASES` 聚合。
- 对应 raw data 模块，如需微调。
- 删除或转为兼容 shim 的旧顶层 family 模块，例如 `cases/*_model.py`、`cases/*_tsp.py`、`cases/*_jobshop.py`。

每个 family 的交付物：

- 实例模块自包含 case、问题描述、建模函数、默认策略声明、`solve_case()`。
- `CASES` 聚合可被 registry 收集。
- 至少一个 smoke case 可通过根入口运行。

每个 family 的验收：

- `python -m benchmarks.run --list-cases` 能看到迁移 case。
- focused smoke 能产生 success row 或 error row。
- row 至少包含 `benchmark_id`、`family`、`tier`、`strategy`、`strategy_profile`、`status`、`feasible`、`objective`、`reference_objective`、`gap_rel`、`elapsed_seconds`。
- MIPLIB exact baseline 与其他 case 保持同一 case/strategy 层级，由策略决定求解方式。

注意事项：

- 允许实例间重复。
- 不新增固定 `model.py` 或 `solve.py`。
- 不创建新的 top-level metadata/cache 目录。

## Phase 6: Cleanup And Documentation

目标：

- 清理旧结构残留。
- 更新开发者文档。
- 确认结果契约和 dashboard 数据契约仍成立。

改动范围：

- README。
- 本文档。
- 可能的 compatibility shim。
- tests 或 focused smoke 命令。

交付物：

- 新增 case 开发指南。
- 根入口使用说明。
- `presentation/` 场景脚本命名和职责说明。
- 移除不再使用的旧顶层 `models/`、`loaders/` 风格引用。

验收：

- `python -m benchmarks.run --list-cases` 通过。
- 至少一个 migrated case focused smoke 通过。
- 若涉及 result-contract 相关代码，运行 focused pytest 或 focused smoke。
- 没有新增 top-level `catalog/`、`definitions/`、`data-cache/`、`models/`、`loaders/`。
- 未意外修改 immutable published result artifacts。

当前完成状态：

- 已新增 `docs/new-case-guide.md`，说明新增 case 的目录、实例模块契约、根入口用法、presentation 边界和验证命令。
- 已更新 compatibility helper 与 raw loader 注释，移除会暗示固定 `model.py` / `solve.py` / `graphmodel.py` 层级的表述。
- `presentation/README.md` 已说明 `benchmarks.run` 是轻量本地入口，`presentation/` 只承载具体目标评测场景。
- README 当前在工作树中处于删除状态；Phase 6 未恢复或改写该文件，以避免覆盖非本阶段变更。

## Global Acceptance Criteria

结构验收：

- 新 case 只需在目标实例模块中声明 case 对象、问题描述、建模函数、默认策略声明和 `solve_case()`。
- `cases/` 下不再需要顶层 family-specific runner 模块承载默认求解逻辑。
- 不新增固定 `model.py` 层。
- 不新增固定 `solve.py` 层。
- `benchmarks/run.py` 或等价根入口可直接调用任意 case，并支持自定义策略测试。
- `presentation/` 下新增文件必须对应具体目标评测场景。

功能验收：

- `python -m benchmarks.run --list-cases` 能列出迁移后的 case。
- 至少一个迁移后的 case 能通过 focused smoke 求解。
- 失败路径写出 error rows，而不是中断整个 suite 或根入口调用。
- result rows 保持当前 contract 需要的字段。

契约验收：

- `docs/result-json-contract.md` 定义的 summary JSON 字段不因 case 基类引入而缺失。
- `docs/dashboard-data-contract.md` 定义的 presentation 数据生成入口不需要扫描 `cases/` 内部实现细节。
- presentation 历史结果只在明确任务要求时修改。

## Confirmed Decisions

- `problem_type` 直接使用目录名；`family` 继续作为结果比较与 dashboard 聚合字段。
- 默认策略预算在具体实例模块中声明固定值，策略声明最终产出公开 OptAgent 策略配置类。
- MIPLIB 等 exact baseline 与其他实例保持同一 case/strategy 层级，不新增 exact baseline 特殊层级。
- `BenchmarkCase` 必须包含 `compare_key` 和 `series_key`。
- 允许实例间逻辑重复，优先保障单实例全流程自包含。
- `presentation/` 不是通用运行层，只服务具体目标评测场景。
