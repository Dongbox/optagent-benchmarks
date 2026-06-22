# OptAgent 建模原生 Benchmark

本仓库维护 OptAgent 的性能评测输入、建模适配和离线评测 harness。在父仓库 `optagent` 中，本仓库以 `benchmarks/` 子模块形式检出，来源为 `https://github.com/Dongbox/optagent-benckmarks.git`。

子模块分支名应与父仓库分支名保持一致。例如父仓库分支 `cpp-python-boundary-redesign` 对应本仓库分支 `cpp-python-boundary-redesign`。

`examples/` 用于展示 API 用法；`benchmarks/` 用于形成可重复的策略、后端和建模路线证据。benchmark 结果可以指导默认策略、搜索算子、预算和并行配置的调整，但不能反向成为 catalog ground truth。

## 固定交互流程

当前 benchmark 交互固定为四段：

1. 数据拉取与 catalog 选择
2. 与数据 family 对应的模型建模
3. 评测主函数声明：加载建模、声明策略、声明比较方式
4. 输出结果与对比报告

### 1. 数据拉取与 catalog 选择

source-of-truth catalog 是：

- `catalog/modeling-native-catalog-v1.json`

在父仓库中，可读快照写到：

- `docs/evals/benchmark-suite/catalogs/modeling-native-catalog-v1.md`

catalog 只记录公开 benchmark 元数据、实例来源、family、tier、外部 reference objective / bound 和 OptAgent 建模声明。它不运行 OptAgent、CP-SAT、HiGHS、OR-Tools 或 OptX。

父仓库中生成 catalog 的命令是：

```bash
./.venv/bin/python scripts/build_modeling_native_benchmark_catalog.py
```

运行 benchmark 时，数据由各 family loader 从公开源或本地缓存读取。默认缓存目录是：

```text
data-cache/
```

`data-cache/` 是本地忽略缓存，普通提交不应包含下载的原始公开实例文件。需要离线或 CI 固定输入时使用 `--no-download`，让缺失缓存直接失败。

### 2. 与数据对应的模型建模

每个 benchmark family 必须有明确的“数据格式 -> OptAgent 建模方式”映射。当前 runner-ready families 为：

| Family | 数据来源/格式 | OptAgent 建模方式 | 主要评测目的 |
| --- | --- | --- | --- |
| `interval_job_shop` | JSPLIB / ScheduleOpt JSON | 每个 operation 一个 `interval_var`，机器 `sequence_var + no_overlap`，工序 `precedence`，目标为 makespan | 调度可行性、修复能力、CP-SAT exact baseline 与 GA/ALNS 的差距 |
| `cumulative_resource_scheduling` | PSPLIB `.rcp` / `.sm` | `interval_var`、`precedence`、可再生资源 `cumulative`，目标为 makespan | 资源约束调度的可行解生成、repair、时间到首个可行解 |
| `sequence_blackbox_tsp` | TSPLIB `.tsp` / `.tsp.gz` | `sequence_var` tour 加确定性 `external_call` tour length；也支持 graph-native `sequence_transition_sum` model style 对比 | 序列搜索、delta/full evaluation 比例、黑盒 callback 成本 |
| `sequence_quadratic_assignment` | QAPLIB `.dat` | `sequence_var` facility-to-location assignment 加确定性 `external_call` quadratic cost | 排列搜索、swap delta、repair 与局部改进收益 |
| `exact_linear_mip` | MIPLIB `.mps` / `.mps.gz` | canonical linear MP，bool/int/float 变量、线性约束、线性目标 | exact backend / OptX baseline，不作为 GA/ALNS/Tabu 主评测域 |

建模代码必须放在 `models/`，只负责构造 OptAgent program 和保留必要的 case metadata；数据解析和下载逻辑必须放在 `loaders/`；策略运行逻辑必须放在 `runners/`。

### 3. 评测主函数声明

统一主入口是：

```bash
PYTHONPATH=build/native-debug:src ./.venv/bin/python -m benchmarks.runners.run
```

主入口对应 Python API：

```python
from benchmarks.runners.suite import run_benchmark_suite
```

评测主函数必须显式声明以下维度：

| 维度 | CLI 参数 | Python 参数 | 说明 |
| --- | --- | --- | --- |
| 问题 family | `--family` | `families` | 不传时默认跑 runner-ready smoke families：JSPLIB、TSPLIB、QAPLIB |
| 规模层级 | `--tier` | `tiers` | `smoke` / `calibration` / `full` |
| 指定 case | `--case` | `benchmark_ids` | 用于聚焦单个实例或回归 case |
| 策略集合 | `--strategy` | `strategies` | 不传时使用 family-aware 默认策略 |
| TSP 建模方式 | `--model-style` | `model_styles` | 可比较 blackbox external call 与 graph-native transition sum |
| 默认策略候选矩阵 | `--default-candidate-matrix` | `default_candidate_matrix` | 用于决定当前默认策略候选 |
| 并行矩阵 | `--parallel-matrix`、`--thread-count` | `parallel_thread_counts` | 用于比较线程扩展性 |
| 预算 | `--max-iterations`、`--time-limit-s`、`--population-size`、`--trace-limit` | 同名参数 | CLI 预算是上限，实际预算按 family/tier ceiling 收敛 |
| 数据缓存 | `--data-cache-dir`、`--no-download` | `data_cache_dir`、`allow_download` | 控制公开实例下载和离线复现 |

默认策略规则：

- 调度 family：有效策略为 `ga`、`alns`；请求 `tabu` 或 `lns` 会替换为 `alns` 并记录到 `strategy_substitutions`。原因是当前 standalone Tabu/LNS 不能稳定产出有价值的调度 benchmark rows。
- 序列 / 排列 family：有效策略为 `ga`、`alns`、`tabu`，也可显式加入 `local_search`。
- MIP family：只输出 `optx` exact baseline row；请求的启发式策略会作为 ignored request metadata 记录。未来如增加 MILP-native heuristic，必须新建专用路线，不能替代 OptX baseline。

### 4. 输出结果

每次运行写入一个不可变目录：

```text
docs/evals/benchmark-suite/runs/<timestamp>/
```

输出文件固定如下：

| 文件 | 格式 | 用途 |
| --- | --- | --- |
| `config.json` | JSON | 本次运行的 family、tier、case、strategy、budget、model style、平台和 Python 信息 |
| `results.jsonl` | JSONL，一行一个 row | 主结果表；策略 row 和 exact baseline row 都在这里 |
| `results.csv` | CSV | 便于人工快速筛选和表格工具查看 |
| `anytime.jsonl` | JSONL | 每个 row 的 checkpoint 曲线，来自 native trace 或 CP-SAT callback samples |
| `throughput.jsonl` | JSONL | moves/evaluations/repairs 等吞吐指标和 per-second rate |
| `summary.json` | JSON | 聚合统计、best_by_case、profile counts、default candidate matrix、parallel matrix |
| `report.md` | Markdown | 人类可读报告 |

`results.jsonl` row 必须保持 schema v2。稳定核心字段包括：

- `benchmark_schema_version`
- `benchmark_id`
- `family`
- `tier`
- `instance`
- `kind`
- `strategy`
- `strategy_profile`
- `budget_profile`
- `model_style`
- `status`
- `feasible`
- `objective`
- `best_cost`
- `reference_objective`
- `reference_cost`
- `reference_kind`
- `gap_abs`
- `gap_rel`
- `elapsed_seconds`
- `runtime_s`
- `time_to_best_seconds`
- `thread_count`
- `parallel_matrix_enabled`
- `effective_budget`

策略 row 可能额外包含：

- `strategy_config`
- `initial_cost`
- `improvement_abs`
- `improvement_rel`
- `improvement_per_second`
- `improvement_per_evaluation`
- `improvement_per_move`
- `moves_attempted`
- `moves_accepted`
- `evaluations`
- `delta_evaluations`
- `full_evaluations`
- `repairs_attempted`
- `repairs_succeeded`
- 对应的 `*_per_s` 速率字段

错误 row 仍必须写入 `results.jsonl`，并带有：

- `status = "error"`
- `feasible = false`
- `error.type`
- `error.message`

这样比较报告才能区分“质量回退”“不可行”“运行错误”和“缺少 case”。

## 目录职责

| 路径 | 职责 |
| --- | --- |
| `README.md` | benchmark 使用入口、交互契约和维护规则 |
| `catalog/` | 版本化 catalog，记录 selected cases、外部 reference 和建模声明 |
| `definitions/<family>/` | family 级 case manifest、实例选择和建模说明 |
| `loaders/` | 公共数据格式 loader，负责下载、缓存、本地读取和规范化数据记录 |
| `models/` | family 级 OptAgent `ModelBuilder` / program 构造 |
| `runners/run.py` | CLI 主入口，解析评测声明并调用 suite |
| `runners/suite.py` | 统一调度器，选择 case、解析预算、分派 family runner、写 artifacts |
| `runners/<family>.py` | family 级运行器，加载数据、建模、声明策略配置、执行求解、生成 row |
| `runners/common.py` | 预算、profile 命名、row 归一化、run dir 和 JSON/JSONL 写入 |
| `runners/telemetry.py` | schema v2 observability、anytime、throughput、improvement 指标归一化 |
| `runners/compare.py` | 两个 run 目录的 row-level/family-level 对比和 curated report |
| `runners/dashboard.py` | 从已有 run artifact 生成静态 dashboard 数据 |
| `data-cache/` | 本地忽略缓存，不作为 catalog ground truth |

不要把 loaders、models、runner 或 run artifact 放进 `examples/`。examples 可以链接 benchmark，但不能成为性能 harness。

## 按场景选择评测

benchmark 不是为了穷举所有参数组合。优先选择能回答策略决策问题的评测，再扩展到更大的矩阵。

### 默认策略候选选择

目的：回答“当前默认策略候选应该是谁”。

使用：

```bash
PYTHONPATH=build/native-debug:src ./.venv/bin/python -m benchmarks.runners.run \
  --tier smoke \
  --default-candidate-matrix \
  --max-iterations 5 \
  --time-limit-s 2 \
  --population-size 8
```

当没有显式 `--strategy` 时，该模式运行：

- `local_search`
- `alns`
- `ga`
- `tabu`

排序策略为 `feasible_coverage_then_error_then_gap_then_time_then_improvement_v1`：先看 family/case 覆盖和可行率，再看 error/non-feasible 率、平均/最大 gap、平均耗时，最后看 improvement/sec。MIP exact baseline row 不参与默认策略候选排序。

这是当前最有决策价值的评测需求。涉及默认策略、搜索算子、repair、预算调整时，优先跑这个矩阵，而不是先做全量长跑。

### 调度可行性和修复能力

目的：评估 job shop / RCPSP 中 GA 与 ALNS 是否能稳定得到可行解，以及与 CP-SAT baseline 的距离。

使用：

```bash
PYTHONPATH=build/native-debug:src ./.venv/bin/python -m benchmarks.runners.run \
  --family interval_job_shop \
  --family cumulative_resource_scheduling \
  --tier smoke \
  --tier calibration \
  --strategy ga \
  --strategy alns \
  --max-iterations 20 \
  --time-limit-s 5 \
  --population-size 16
```

重点看：

- `feasible`
- `gap_rel`
- `time_to_first_feasible_seconds`
- `time_to_best_seconds`
- `repairs_attempted_per_s`
- `repairs_succeeded_per_s`
- `ga_scheduling_repair_count`
- `alns_repair_applications`

### 序列 / 排列搜索质量

目的：比较 TSP/QAP 上 GA、ALNS、Tabu 的质量、吞吐、delta evaluation 与局部改进效果。

使用：

```bash
PYTHONPATH=build/native-debug:src ./.venv/bin/python -m benchmarks.runners.run \
  --family sequence_blackbox_tsp \
  --family sequence_quadratic_assignment \
  --tier smoke \
  --tier calibration \
  --strategy ga \
  --strategy alns \
  --strategy tabu \
  --max-iterations 20 \
  --time-limit-s 5 \
  --population-size 16
```

重点看：

- `gap_rel`
- `improvement_per_second`
- `evaluations_per_s`
- `delta_evaluations_per_s`
- `full_evaluations_per_s`
- `sequence_graph_delta_count`
- `qap_swap_delta_count`

### TSP 建模方式对比

目的：比较 blackbox `external_call` 与 graph-native `sequence_transition_sum` 对搜索性能的影响。

使用：

```bash
PYTHONPATH=build/native-debug:src ./.venv/bin/python -m benchmarks.runners.run \
  --family sequence_blackbox_tsp \
  --tier smoke \
  --strategy ga \
  --strategy alns \
  --strategy tabu \
  --model-style sequence_var_external_call \
  --model-style sequence_var_sequence_transition_sum \
  --max-iterations 20 \
  --time-limit-s 5
```

重点看：

- 同一 `benchmark_id`、同一 `strategy` 下不同 `model_style` 的 `gap_rel`
- `runtime_s`
- `evaluations_per_s`
- `delta_evaluations_per_s`
- `full_evaluations_per_s`

### 并行扩展性

目的：比较同一策略在不同 thread count 下的速度、效率和质量变化。

使用默认线程矩阵：

```bash
PYTHONPATH=build/native-debug:src ./.venv/bin/python -m benchmarks.runners.run \
  --family sequence_blackbox_tsp \
  --tier smoke \
  --strategy ga \
  --parallel-matrix \
  --max-iterations 5 \
  --time-limit-s 2
```

使用自定义线程矩阵：

```bash
PYTHONPATH=build/native-debug:src ./.venv/bin/python -m benchmarks.runners.run \
  --family sequence_blackbox_tsp \
  --tier smoke \
  --strategy ga \
  --thread-count 1 \
  --thread-count 4 \
  --thread-count 8
```

重点看 `summary.json` 中的 `parallel_matrix`：

- `speedup`
- `efficiency`
- `quality_delta_vs_1_thread`
- `throughput_speedup`

默认策略候选排序只使用 1-thread strategy rows，避免并行 rows 影响默认单线程策略选择。

### MIP exact backend baseline

目的：验证 canonical MP / MPS exact backend 路线和 OptX 行为，不评估 GA/ALNS/Tabu。

使用：

```bash
PYTHONPATH=build/native-debug:src ./.venv/bin/python -m benchmarks.runners.run \
  --family exact_linear_mip \
  --tier smoke \
  --time-limit-s 10
```

重点看：

- `status`
- `feasible`
- `objective`
- `gap_rel`
- `metadata.best_bound`
- `metadata.mip_gap`
- `metadata.node_count`
- `metadata.simplex_iteration_count`

## 对比两个 run

比较两个不可变 run 目录：

```bash
PYTHONPATH=build/native-debug:src ./.venv/bin/python -m benchmarks.runners.compare \
  docs/evals/benchmark-suite/runs/<baseline> \
  docs/evals/benchmark-suite/runs/<candidate> \
  --format markdown
```

写入 curated report 和 ledger：

```bash
PYTHONPATH=build/native-debug:src ./.venv/bin/python -m benchmarks.runners.compare \
  docs/evals/benchmark-suite/runs/<baseline> \
  docs/evals/benchmark-suite/runs/<candidate> \
  --report-id <stable-id> \
  --baseline-commit <baseline-commit> \
  --candidate-commit <candidate-commit> \
  --decision accepted \
  --follow-up "<action>"
```

对比逻辑按 row key 匹配：

```text
benchmark_id + family + strategy + strategy_profile + model_style + kind
```

比较报告会输出：

- objective delta
- gap delta
- elapsed seconds delta
- time-to-best delta
- improvement/sec delta
- throughput delta
- family summary
- candidate vs reference summary
- gate status

## 静态 dashboard

从已有 run artifact 生成 dashboard，不重新运行 benchmark：

```bash
PYTHONPATH=build/native-debug:src ./.venv/bin/python -m benchmarks.runners.dashboard \
  docs/evals/benchmark-suite/runs/<candidate> \
  --baseline-dir docs/evals/benchmark-suite/runs/<baseline> \
  --dashboard-id <stable-id>
```

父仓库输出目录：

```text
docs/evals/benchmark-suite/dashboards/<stable-id>/
```

输出文件：

- `dashboard.json`
- `anytime-curves.json`
- `dashboard.md`

## Source Policy

catalog reference objective 和 bound 必须来自公开 benchmark 来源，不能来自本地 OptAgent run。

本地 run 可以用于：

- regression comparison
- default strategy candidate evidence
- family-specific strategy tuning
- release gate evidence
- dashboard 和 curated report

本地 run 不可以用于：

- 覆盖 catalog ground truth
- 把一次本地求解结果写成 `optimal`
- 在产品 `solve(...)` 路径中隐式触发 benchmark 或自动调参

## 最小验证

文档或 harness 结构变更后，至少运行：

```bash
PYTHONPATH=build/native-debug:src ./.venv/bin/python -m pytest -q \
  tests/test_benchmark_suite_catalog.py \
  tests/test_benchmark_telemetry.py
```

涉及 runner 行为、策略 row、输出 schema 或比较报告时，增加：

```bash
PYTHONPATH=build/native-debug:src ./.venv/bin/python -m pytest -q \
  tests/test_benchmark_suite_runner.py \
  tests/test_benchmark_suite_jsplib_runner.py \
  tests/test_benchmark_suite_rcpsp_runner.py \
  tests/test_benchmark_suite_qap_runner.py \
  tests/test_benchmark_suite_miplib_runner.py
```

涉及 native search、public solve route、trace、metadata 或 C++/Python 边界时，必须同时确认 native build tree 被加载，父仓库推荐入口是：

```bash
PYTHONPATH=build/native-debug:src ./.venv/bin/python -m pytest -q <focused-tests>
```
