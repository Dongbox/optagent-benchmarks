# cases 目录说明

`cases/` 是 benchmark 的用例声明层。它不保存 dashboard 结果，而是定义
`benchmarks.run`、suite runner 和 dashboard 都能理解的同一类对象：
一个具体问题实例的元数据、规模、参考值、OptAgent 建模代码和结果解码逻辑。

当前目录既包含公开 benchmark 数据集，也包含自定义 benchmark。公开数据集通常按
“来源库 / 问题类型 / 系列实例”组织；自定义 benchmark 应优先表达问题建模和规模，
不要为了复用现有目录风格而伪装成 TSPLIB、JSPLIB 这类外部数据集。

## 当前结构

```text
cases/
  base.py                         # BenchmarkCase 契约和 row 转换
  common.py                       # family/model_style/strategy_profile 等共享语义
  registry.py                     # run.py 使用的 collection package 注册表

  custom/
    steel_transition_sequence/
      _domain.py                  # steel 问题建模、数据读取、case 工厂
      toy.py                      # toy 规模实例声明
      bundled.py                  # bundled_head40 / bundled 实例声明
      data/steel_coils.json       # benchmark 自有输入数据

  tsplib/tsp/
    _domain.py                    # TSPLIB TSP 解析、建模、case 工厂
    berlin.py
    pr.py
    raw/

  jsplib/jobshop/
    _domain.py
    ft.py
    la.py
    raw/

  psplib/rcpsp/
    _domain.py
    j90_1.py
    raw/

  qaplib/quadratic_assignment/
    _domain.py
    nug.py
    raw/

  miplib2017/linear_mip/
    _domain.py
    reblock.py
    raw/
```

常见公开数据集结构是：

```text
cases/<source>/<instance_type>/
  _domain.py       # 同一来源和问题类型的解析、建模、工厂函数
  <series>.py      # 一个或多个具体 BenchmarkCase 声明
  __init__.py      # 汇总子模块的 CASES
  raw/             # 原始实例文件或本地缓存
```

自定义 benchmark 可以采用更贴近问题的结构，例如当前 steel 示例：

```text
cases/custom/steel_transition_sequence/
  _domain.py
  toy.py
  bundled.py
  data/steel_coils.json
```

这个结构的含义是：`custom` 表示非公开标准库来源；`steel_transition_sequence`
表示问题建模形式；`toy.py`、`bundled.py` 表示不同规模或系列的具体实例声明。
这类结构类似 MiniZinc benchmark 的做法：目录优先说明“问题是什么、实例规模如何”，
而不是围绕某个外部文件格式解析器来命名。

## BenchmarkCase 声明格式

每个可运行实例最终都应该是一个 `BenchmarkCase` 对象。通常做法是在 `_domain.py`
里定义子类和工厂函数，在具体实例文件里只声明数据。

`BenchmarkCase` 的核心字段：

```python
BenchmarkCase(
    benchmark_id="custom_steel_sequence_toy",
    source="OptAgent custom",
    problem_type="production",
    instance_type="steel_transition_sequence",
    instance="toy",
    family="sequence_transition_penalty",
    tier="smoke",
    size={"nodes": 5, "coils": 5},
    data={"data_path": ".../steel_coils.json"},
    reference={"objective": 3, "status": "optimal", "value_kind": "optimal"},
    problem_description="...",
    case_module=__name__,
    modeling_notes={
        "model_style": "sequence_var_external_transition_penalty",
        "objective_sense": "minimize",
        "public_api_primitives": ["sequence_var", "external_call"],
    },
)
```

字段约定：

- `benchmark_id`：全局唯一、小写、带来源前缀，例如 `custom_steel_sequence_toy`、
  `tsplib_berlin52`、`jsplib_ft06`。
- `source`：数据来源。公开库写库名；自定义数据可以写 `OptAgent custom` 或更明确的业务来源。
- `problem_type`：广义问题类别，例如 `production`、`routing`、`scheduling`、`assignment`。
- `instance_type`：具体问题变体，例如 `steel_transition_sequence`、`tsp`、`jobshop`。
- `family`：runner 用来选择默认策略和配置的语义族。新增语义族需要注册到
  `cases/registry.py`，必要时也要更新 `run.py`。
- `tier`：评估层级，通常是 `smoke`、`calibration`、`full`。
- `size`：稳定规模信息。序列类问题建议至少提供 `nodes`，因为默认策略配置会用它估算维度。
- `data`：复现实例所需的路径、URL 或生成参数。不要放求解结果。
- `reference`：最优值、best-known、baseline 或 bound。没有证明最优时，明确写
  `value_kind`，例如 `baseline`、`best_known`、`lower_bound`、`unknown`。
- `case_module`：实例声明模块内固定写 `__name__`。
- `modeling_notes`：描述建模风格、目标方向和用到的公开 OptAgent primitive。

## _domain.py 的作用

`_domain.py` 不是强制架构，而是为了把同一问题类型下的重复逻辑收敛到一处。它通常包含：

- `SOURCE`、`SOURCE_KEY`、`PROBLEM_TYPE`、`INSTANCE_TYPE`、`FAMILY`、`MODEL_STYLE`
  等常量。
- 数据读取、格式解析或实例生成逻辑。
- 领域 dataclass，例如 `SteelCoilInstance`。
- `BenchmarkCase` 子类，至少实现 `build_model()`；需要解码解或重算目标值时实现
  `solution_metrics()`。
- 工厂函数，例如 `make_steel_case(...)`，统一填充元数据、`compare_key`、
  `series_key`、`reference` 和 dashboard 需要的说明字段。

当前 steel case 的 `_domain.py` 做了这些事：

- 从 `data/steel_coils.json` 读取 `toy`、`bundled_head40`、`bundled` 三个实例。
- 用 `can_weld(...)` 判断相邻钢卷是否可直接焊接。
- 构建 0/1 `penalty_matrix`，不可直接焊接的相邻转移罚 1。
- 用 `sequence_var` 表示钢卷顺序。
- 用 `external_call` 调用 transition penalty evaluator，最小化相邻不兼容转移次数。
- 在 `solution_metrics()` 中解码序列、重算 objective，并输出 weld ratio 等诊断信息。
  `sequence_head` 等展示截断字段由 `presentation/` 从 `decoded_solution` 派生。

## 新增 case 的接入步骤

如果加入已有 collection，例如给 `tsplib/tsp` 增加实例：

1. 新增 `cases/tsplib/tsp/<series>.py`。
2. 在文件内声明 case，并暴露 `CASES = (MY_CASE,)`。
3. 在 `cases/tsplib/tsp/__init__.py` import 该模块。
4. 把 `*<series>.CASES` 加入包级 `CASES` 元组。

如果新增一个新的 custom collection，例如另一个自定义生产问题：

1. 新建 `cases/custom/<problem_name>/__init__.py` 和必要的 `_domain.py`、实例声明文件。
2. 在该 collection 的 `__init__.py` 聚合所有子模块的 `CASES`。
3. 在 `cases/registry.py` 的 `INSTANCE_COLLECTION_MODULES` 中加入包路径，例如
   `"benchmarks.cases.custom.steel_transition_sequence"`。
4. 如果引入新 `family`，把 family 名加入 `IMPLEMENTED_FAMILY_NAMES`。
5. 如果新 family 需要默认策略，在 `run.py` 的 `default_strategy_names_for_family()`
   中声明；如果策略参数需要特殊处理，再更新 `build_strategy_config()`。
6. 如果 dashboard 或 suite 需要按 family 显示模型风格，在 `cases/common.py` 的
   `MODEL_STYLE_BY_FAMILY` 中补充映射。

`run.py` 不逐个 import 具体 case。实际发现链路是：

```text
benchmarks.run
  -> benchmarks.cases.registry.benchmark_case_objects()
  -> INSTANCE_COLLECTION_MODULES
  -> collection package 的 CASES
  -> 具体实例模块的 CASES
```

## steel custom case 示例

当前 steel benchmark 已真实接入在 `cases/custom/steel_transition_sequence/`。

实例声明文件 `toy.py` 的形态：

```python
from __future__ import annotations

from benchmarks.cases.custom.steel_transition_sequence._domain import make_steel_case

CASE_MODULE = __name__

TOY = make_steel_case(
    instance="toy",
    tier="smoke",
    coils=5,
    reference={
        "objective": 3,
        "status": "optimal",
        "value_kind": "optimal",
        "notes": "The five-coil toy instance is small enough to verify by exhaustive permutation.",
    },
    case_module=CASE_MODULE,
)

CASES = (TOY,)
```

`bundled.py` 声明了两个更大规模：

- `custom_steel_sequence_bundled_head40`：40 个钢卷，`tier="calibration"`。
- `custom_steel_sequence_bundled`：285 个钢卷，`tier="full"`。

这两个 bundled reference 目前是自然输入顺序的 baseline，而不是证明最优值：

```python
reference={
    "objective": 22,
    "status": "baseline",
    "value_kind": "baseline",
    "notes": "Baseline is the natural bundled data order from the steel example.",
}
```

这个区别很重要：runner 会计算 `objective - reference`，dashboard 也会展示
`reference_kind`。如果 reference 不是最优值，必须明确写成 `baseline` 或
`best_known`，避免把改进空间误读成最优 gap。

## 校验命令

新增或修改 case 后，至少运行：

```bash
python -m compileall cases presentation
PYTHONPATH=.. python -m benchmarks.run --list-cases
PYTHONPATH=.. python -m benchmarks.run --case custom_steel_sequence_toy --max-iterations 1 --time-limit-s 0.1
```

如果改动会进入 dashboard 数据，还要运行：

```bash
PYTHONPATH=.. python -m benchmarks.presentation.generate_dashboard_data --check
```

不要手工编辑 `presentation/results/index.json` 或
`presentation/aggregates/*.json`；需要通过生成流程更新。
