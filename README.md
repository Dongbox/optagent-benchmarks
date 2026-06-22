# OptAgent 公共接口 Benchmark

本仓库维护面向 OptAgent 发布包的性能评测输入、建模适配和离线评测 harness。使用者的默认工作方式是：先在 Python 环境中安装已经打包发布的 `optagent` wheel，再运行本仓库 `benchmarks` 包中的评测脚本。

本仓库也可以作为 `optagent` 主仓库的 `benchmarks/` 子模块检出。作为子模块使用时，分支名应与主仓库分支名保持一致。例如主仓库分支 `cpp-python-boundary-redesign` 对应本仓库分支 `cpp-python-boundary-redesign`。

`examples/` 用于展示 API 用法；`benchmarks/` 用于形成可重复的策略、后端和建模方式证据。benchmark 结果可以指导默认策略、搜索算子、预算和并行配置的调整，但不能反向成为 catalog ground truth。

## 安装与运行前提

benchmark 面向安装后的 `optagent` Python 库运行，不要求使用 `optagent` 源码 checkout 或开发构建目录。

推荐环境：

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install <path-or-url-to-optagent-wheel>
python -m pip install pytest
```

如果从主仓库 checkout 运行，需要先初始化本仓库子模块：

```bash
git submodule update --init benchmarks
```

运行命令应从包含 `benchmarks/` 包的工作目录执行：

```bash
python -m benchmarks.runners.run --tier smoke
```

不要通过源码路径覆盖已安装的 `optagent` 包来运行本 benchmark。该方式属于开发验证，不是面向发布 wheel 的性能评测入口。

## 公开接口边界

本仓库只通过 `optagent` 的公开 Python 接口交互：

- 建模接口：`ModelBuilder` 暴露的变量、约束、目标和 `external_call` 建模能力。
- 求解接口：`solve(...)`、`solve_cpsat(...)`、`solve_milp(...)`。
- 策略配置：`LocalSearchConfig`、`TabuConfig`、`LnsConfig`、`AlnsConfig`、`GaConfig`、`CpSatConfig`、`MilpConfig`。
- 结果读取：公开 solution 对象上的 `status`、`feasible`、`objective_value`、`variable_values`、`solver_name`、`metadata`。

本仓库自定义模块的边界：

- `loaders/` 负责公开 benchmark 数据的下载、缓存、解析和规范化。
- `models/` 负责把规范化数据映射成公开 OptAgent 建模接口调用。
- `runners/` 负责声明策略配置、调用公开求解接口、计算 benchmark 指标和写出结果。
- `catalog/` 和 `definitions/` 负责记录评测 case、来源、tier、reference objective / bound 和建模声明。

本仓库不依赖也不描述 OptAgent 实现细节。文档中的策略、建模和求解行为应以公开 API 可见行为为准。

## 固定交互流程

当前 benchmark 交互固定为四段：

1. 数据拉取与 catalog 选择
2. 与数据 family 对应的模型建模
3. 评测主函数声明：加载建模、声明策略、声明比较方式
4. 输出结果与对比报告

### 1. 数据拉取与 catalog 选择

source-of-truth catalog 是：

- `catalog/modeling-native-catalog-v1.json`

可读 catalog 快照建议写到：

- `docs/evals/benchmark-suite/catalogs/modeling-native-catalog-v1.md`

catalog 只记录公开 benchmark 元数据、实例来源、family、tier、外部 reference objective / bound 和公开 OptAgent API 建模声明。它不运行任何求解器。

catalog 随本仓库版本维护。普通 wheel 评测使用已提交的 catalog，不需要重新生成；只有维护者调整 case selection、reference 来源或 family manifest 时，才需要通过配套维护脚本重新生成并审查 diff。

运行 benchmark 时，数据由各 family loader 从公开源或本地缓存读取。默认缓存目录是：

```text
data-cache/
```

`data-cache/` 是本地忽略缓存，普通提交不应包含下载的原始公开实例文件。需要离线或 CI 固定输入时使用 `--no-download`，让缺失缓存直接失败。

### 2. 与数据对应的模型建模

每个 benchmark family 必须有明确的“数据格式 -> 公开 OptAgent API 建模方式”映射。当前 runner-ready families 为：

| Family | 数据来源/格式 | 公开 API 建模方式 | 主要评测目的 |
| --- | --- | --- | --- |
| `interval_job_shop` | JSPLIB / ScheduleOpt JSON | 每个 operation 一个 `interval_var`，机器 `sequence_var + no_overlap`，工序 `precedence`，目标为 makespan | 调度可行性、修复能力、CP-SAT exact baseline 与 GA/ALNS 的差距 |
| `cumulative_resource_scheduling` | PSPLIB `.rcp` / `.sm` | `interval_var`、`precedence`、可再生资源 `cumulative`，目标为 makespan | 资源约束调度的可行解生成、repair、时间到首个可行解 |
| `sequence_blackbox_tsp` | TSPLIB `.tsp` / `.tsp.gz` | `sequence_var` tour 加确定性 `external_call` tour length；也支持基于公开建模表达的 graph-style model style 对比 | 序列搜索、求值吞吐、黑盒 callback 成本 |
| `sequence_quadratic_assignment` | QAPLIB `.dat` | `sequence_var` facility-to-location assignment 加确定性 `external_call` quadratic cost | 排列搜索、swap delta、repair 与局部改进收益 |
| `exact_linear_mip` | MIPLIB `.mps` / `.mps.gz` | 公开线性 MIP 建模接口，bool/int/float 变量、线性约束、线性目标 | `solve_milp(...)` baseline，不作为 GA/ALNS/Tabu 主评测域 |

建模代码必须放在 `models/`，只负责调用公开 OptAgent 建模接口并保留必要的 case metadata；数据解析和下载逻辑必须放在 `loaders/`；策略运行逻辑必须放在 `runners/`。

### 3. 评测主函数声明

统一主入口是：

```bash
python -m benchmarks.runners.run
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
| TSP 建模方式 | `--model-style` | `model_styles` | 可比较 blackbox external call 与图表达 model style |
| 默认策略候选矩阵 | `--default-candidate-matrix` | `default_candidate_matrix` | 用于决定当前默认策略候选 |
| 并行矩阵 | `--parallel-matrix`、`--thread-count` | `parallel_thread_counts` | 用于比较线程扩展性 |
| 多 seed 校准 | `--calibration-seed` | `run_calibration_suite(seeds=...)` | 重复传入 seed 后运行 calibration wrapper，默认 tier 为 `calibration` |
| 预算 | `--max-iterations`、`--time-limit-s`、`--population-size`、`--trace-limit` | 同名参数 | CLI 预算是上限，实际预算按 family/tier ceiling 收敛 |
| 数据缓存 | `--data-cache-dir`、`--no-download` | `data_cache_dir`、`allow_download` | 控制公开实例下载和离线复现 |

默认策略规则：

- 调度 family：有效策略为 `ga`、`alns`；请求 `tabu` 或 `lns` 会替换为 `alns` 并记录到 `strategy_substitutions`。原因是当前 standalone Tabu/LNS 不能稳定产出有价值的调度 benchmark rows。
- 序列 / 排列 family：有效策略为 `ga`、`alns`、`tabu`，也可显式加入 `local_search`。
- MIP family：只输出 `solve_milp(...)` exact baseline row；请求的启发式策略会作为 ignored request metadata 记录。未来如增加 MILP 启发式评测，必须新建专用 benchmark 路线，不能替代 exact baseline。

### 4. 输出结果

每次运行写入一个不可变目录：

```text
docs/evals/benchmark-suite/runs/<timestamp>/
```

输出文件固定如下：

| 文件 | 格式 | 用途 |
| --- | --- | --- |
| `config.json` | JSON | 本次运行的 family、tier、case、strategy、budget、model style、平台和 Python 信息 |
| `inventory.json` | JSON | 不执行求解器即可读取的 family、case、策略矩阵、row schema 和预算 inventory |
| `run_metadata.json` | JSON | Python、平台、native extension 路径和 git/worktree 元数据 |
| `rows.jsonl` | JSONL，一行一个 row | 规范化主结果表；策略 row 和 exact baseline row 都在这里 |
| `results.jsonl` | JSONL，一行一个 row | `rows.jsonl` 的兼容别名，供旧 dashboard / compare 工具读取 |
| `results.csv` | CSV | 便于人工快速筛选和表格工具查看 |
| `anytime.jsonl` | JSONL | 每个 row 的 checkpoint 曲线，来自公开结果 metadata 或 CP-SAT callback samples |
| `curves.jsonl` | JSONL | `anytime.jsonl` 的规范命名别名 |
| `throughput.jsonl` | JSONL | moves/evaluations/repairs 等吞吐指标和 per-second rate |
| `strategy_feedback.json` | JSON | 按 family / model style 聚合的推荐候选，解析到 typed strategy config 或 direct exact API |
| `summary.json` | JSON | 聚合统计、best_by_case、profile counts、default candidate matrix、parallel matrix、regression gates、strategy feedback |
| `report.md` | Markdown | 人类可读报告，包含 budgets、gates 和 feedback 摘要 |

多 seed 校准入口会创建一个父目录，父目录下每个 seed 是一次完整 run：

```bash
python -m benchmarks.runners.run \
  --family sequence_blackbox_tsp \
  --tier calibration \
  --case tsplib_tiny4 \
  --strategy ga \
  --calibration-seed 11 \
  --calibration-seed 12 \
  --calibration-seed 13
```

父目录额外写出：

| 文件 | 格式 | 用途 |
| --- | --- | --- |
| `rows.jsonl` | JSONL | 所有 seed 子 run 的规范化 row 聚合 |
| `calibration_summary.json` | JSON | 多 seed median / best / worst / failure count、regression gates 和 artifact 索引 |
| `strategy_feedback.json` | JSON | 基于多 seed 聚合证据生成的策略反馈 |

`strategy_feedback.json` 只用于推荐和诊断，不覆盖用户显式传入的
`--strategy` 或 Python `strategy=...`。

`rows.jsonl` row 必须保持 schema v2。`results.jsonl` 在迁移期保持同样内容。稳定核心字段包括：

- `benchmark_schema_version`
- `benchmark_id`
- `family`
- `problem_family`
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
- `route_decision`
- `curve_summary`

策略 row 可能额外包含：

- `strategy_config`
- `family_exact_only`
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
- GA / external objective observability fields where available, including
  `ga_offspring_generated`, `ga_offspring_evaluated`,
  `ga_duplicate_child_count`, `ga_duplicate_ratio`,
  `external_rows_requested`, `external_cache_hits`,
  `external_duplicate_rows_coalesced`, and `external_evaluation_mode`

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
| `models/` | family 级公开 OptAgent 建模接口调用和 program 构造 |
| `runners/run.py` | CLI 主入口，解析评测声明并调用 suite |
| `runners/suite.py` | 统一调度器，选择 case、解析预算、分派 family runner、写 artifacts |
| `runners/<family>.py` | family 级运行器，加载数据、建模、声明策略配置、执行求解、生成 row |
| `runners/common.py` | 预算、profile 命名、row 归一化、run dir 和 JSON/JSONL 写入 |
| `runners/telemetry.py` | schema v2 observability、anytime、throughput、improvement 指标归一化 |
| `runners/compare.py` | 两个 run 目录的 row-level/family-level 对比和 curated report |
| `runners/dashboard.py` | 从已有 run artifact 生成静态 dashboard 数据 |
| `data-cache/` | 本地忽略缓存，不作为 catalog ground truth |

不要把 loaders、models、runner 或 run artifact 放进 `examples/`。examples 可以链接 benchmark，但不能成为性能 harness。

## 开发者快速入口

`optagent-benchmarks` 需要持续人工添加数据、建模和求解评测逻辑。文件增多后，不应要求新开发者先理解所有目录。按任务类型选择入口：

| 任务 | 优先阅读/修改 | 不应先改 |
| --- | --- | --- |
| 在已有 family 下加一个 case | `definitions/<family>/manifest.json`、`catalog/modeling-native-catalog-v1.json` | `models/`、`runners/` |
| 新增一种公开数据格式解析 | `loaders/<family>.py`、对应 loader tests | strategy 配置 |
| 调整公开 API 建模方式 | `models/<family>.py`、对应 model/runner tests | catalog reference objective |
| 新增或调整策略评测 | `runners/<family>.py`、`runners/suite.py` | loader 数据语义 |
| 新增完整 family | `definitions/`、`loaders/`、`models/`、`runners/`、tests、README | Dashboard 页面 |
| 调整结果字段 | `runners/telemetry.py`、`runners/common.py`、`docs/result-json-contract.md` | 单个 family 私有字段 |

### 加已有 family 的新 case

优先路径：

1. 在 `definitions/<family>/manifest.json` 增加 case。
2. 在 catalog 中登记 `benchmark_id`、`family`、`tier`、`instance`、公开来源和 reference。
3. 用已有 loader 验证数据能读取。
4. 跑该 family 的 focused runner test 或 smoke run。

只要数据格式和建模方式没有变化，不要改 `models/` 或 `runners/`。

新增 case 必须回答：

- 数据来源是否公开、可复现？
- reference objective / bound 来自哪里？
- 该 case 属于 `smoke`、`calibration` 还是 `full`？
- 是否需要本地缓存，`--no-download` 下行为是否清晰？

### 新增 family

新增 family 时，固定文件清单是：

```text
definitions/<family>/manifest.json
loaders/<family>.py
models/<family>.py
runners/<family>.py
tests/test_benchmark_suite_<family>_runner.py
```

还需要更新：

```text
runners/suite.py
README.md
catalog/modeling-native-catalog-v1.json
```

新增 family 必须先写清楚：

- 数据格式是什么？
- 对应哪些公开 OptAgent 建模 API？
- 哪些 strategy 合理？
- 哪些 strategy 不应纳入默认比较？
- exact baseline 是否存在？
- Dashboard 中应该归到哪个 group，例如 `scheduling`、`routing`、`packing`、`assignment` 或 `exact-regression`？

### 新增策略评测

新增策略评测不等于新增 strategy 名称。必须先确认该策略对当前 family 有业务意义。

策略评测 PR 必须说明：

- 使用哪个公开 strategy config？
- 与现有 GA / ALNS / Tabu / Local Search / exact baseline 的比较目的是什么？
- 应看哪些指标：`gap_rel`、`runtime_ms`、`feasible`、`time_to_best`、`evaluations_per_s` 还是 `improvement_per_second`？
- 是否进入默认策略候选矩阵？

### 推荐后续工具

为降低上手成本，仓库后续应提供轻量 CLI：

```bash
python -m benchmarks.cli list-families
python -m benchmarks.cli list-cases --family interval_job_shop
python -m benchmarks.cli explain-family interval_job_shop
python -m benchmarks.cli scaffold-case --family interval_job_shop --case my_case
python -m benchmarks.cli scaffold-family --family my_family
python -m benchmarks.cli validate-case --case my_case
```

这些命令的目标不是替代代码审查，而是让开发者快速知道“下一步该改哪个文件”。

### 结果 JSON 契约

Dashboard 使用的长期事实文件不是 Markdown 报告，而是 `results/` 下的 JSON。当前固定：

- 契约文档：`docs/result-json-contract.md`
- Dashboard 数据契约：`docs/dashboard-data-contract.md`
- JSON Schema：`results/schema/run-v1.schema.json`
- 真实 run summary：`results/<group>/<strategy>/<year>/<month>/*.json`
- 入口索引：`results/index.json`
- 聚合数据：`aggregates/*.json`

新增结果字段或 artifact 时，先更新契约和 sample，再更新生成逻辑。不要直接让 Dashboard 读取 runner 私有字段。

新增 run summary 后，重新生成 dashboard 数据：

```bash
python -m benchmarks.runners.generate_dashboard_data
```

提交前可以只做检查：

```bash
python -m benchmarks.runners.generate_dashboard_data --check
```

### GitHub Actions 发布链路

Phase 4 的自动化拆成三个仓库内的 workflow：

| 仓库 | Workflow | 职责 |
| --- | --- | --- |
| `optagent` | `.github/workflows/trigger-benchmark-dashboard.yml` | 从 OptAgent commit dispatch `optagent-benchmarks` benchmark run |
| `optagent-benchmarks` | `.github/workflows/run-benchmarks.yml` | 构建/安装 OptAgent wheel、运行 smoke benchmark、写入 `results/` run summary、重新生成 `results/index.json` 和 `aggregates/*.json` |
| `optagent-benchmarks` | `.github/workflows/publish-results-index.yml` | 手动或结果变更后重新生成 generated dashboard data |
| `optagent-dashboard` | `.github/workflows/deploy-dashboard.yml` | 同步 `results/` 和 `aggregates/` 到 `public/data`、执行 `npm run build`、发布 Cloudflare Pages |

`run-benchmarks.yml` 写入事实层时只应新增 run summary / artifact 文件，并更新 generated index / aggregates。不要修改历史 run summary。

跨仓触发需要 GitHub Actions secrets：

- `OPTAGENT_BENCHMARKS_WORKFLOW_TOKEN`：配置在 `optagent`，允许 dispatch `Dongbox/optagent-benckmarks` workflow。
- `OPTAGENT_REPOSITORY_TOKEN`：配置在 `optagent-benchmarks`，当 OptAgent 仓库 checkout 需要额外权限时使用。
- `OPTAGENT_DASHBOARD_WORKFLOW_TOKEN`：配置在 `optagent-benchmarks`，允许 dispatch `Dongbox/optagent-dashboard` workflow。
- `OPTAGENT_BENCHMARKS_READ_TOKEN`：配置在 `optagent-dashboard`，当 benchmark 仓库 checkout 需要额外权限时使用。
- `CLOUDFLARE_ACCOUNT_ID` / `CLOUDFLARE_API_TOKEN` / `CLOUDFLARE_PAGES_PROJECT`：配置在 `optagent-dashboard`，用于 Cloudflare Pages Direct Upload。

手动验证入口：

```bash
gh workflow run run-benchmarks.yml \
  --repo Dongbox/optagent-benckmarks \
  --ref cpp-python-boundary-redesign \
  -f optagent_repository=Dongbox/optagent \
  -f optagent_ref=<optagent-commit> \
  -f tier=smoke \
  -f family=sequence_blackbox_tsp \
  -f strategy=ga
```

## 按场景选择评测

benchmark 不是为了穷举所有参数组合。优先选择能回答策略决策问题的评测，再扩展到更大的矩阵。

### 默认策略候选选择

目的：回答“当前默认策略候选应该是谁”。

使用：

```bash
python -m benchmarks.runners.run \
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

### 内部 GA 优化验证

目的：验证 GA 内部策略优化是否真的提升有效搜索，而不是只提升原始子代生成数。

该入口消费已有 fixed wall-clock FJSP summary，以及 benchmark suite 的
`rows.jsonl` / `results.jsonl`，生成 Phase 6 报告：

```bash
python -m benchmarks.runners.phase6_internal_ga \
  --fjsp-summary baseline=docs/evals/fjsp-ga-wallclock-1s-seed31/summary.json \
  --fjsp-summary unique_resampling=docs/evals/fjsp-ga-wallclock-1s-unique-resampling/summary.json \
  --suite-run-dir baseline=docs/evals/benchmark-suite/runs/tsp-qap-baseline \
  --suite-run-dir unique_resampling=docs/evals/benchmark-suite/runs/tsp-qap-unique-resampling
```

输出：

- `phase6_internal_ga_report.json`
- `phase6_internal_ga_report.md`

重点看：

- `unique_offspring_per_s`
- `offspring_evaluated_per_s`
- `duplicate_ratio`
- `external_callback_count`
- `external_callback_wall_time_ms`
- `objective_median_delta`
- `gates.overall_status`

Phase 6 gate 要求覆盖 FJSP、小型非 FJSP sequence、QAP-supported case，并且 unknown external callback 只能保持 serial-safe 路径。

### 调度可行性和修复能力

目的：评估 job shop / RCPSP 中 GA 与 ALNS 是否能稳定得到可行解，以及与 CP-SAT baseline 的距离。

使用：

```bash
python -m benchmarks.runners.run \
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
python -m benchmarks.runners.run \
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

目的：比较 blackbox `external_call` 与基于公开图表达的 `sequence_transition_sum` model style 对搜索性能的影响。

使用：

```bash
python -m benchmarks.runners.run \
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
python -m benchmarks.runners.run \
  --family sequence_blackbox_tsp \
  --tier smoke \
  --strategy ga \
  --parallel-matrix \
  --max-iterations 5 \
  --time-limit-s 2
```

使用自定义线程矩阵：

```bash
python -m benchmarks.runners.run \
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

目的：验证通过公开 `solve_milp(...)` 接口运行线性 MIP / MPS case 的 exact baseline 行为，不评估 GA/ALNS/Tabu。

使用：

```bash
python -m benchmarks.runners.run \
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
python -m benchmarks.runners.compare \
  docs/evals/benchmark-suite/runs/<baseline> \
  docs/evals/benchmark-suite/runs/<candidate> \
  --format markdown
```

写入 curated report 和 ledger：

```bash
python -m benchmarks.runners.compare \
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

面向独立 `optagent-dashboard` 仓库的长期数据入口是：

```bash
python -m benchmarks.runners.generate_dashboard_data
```

该命令从 `results/` 的不可变 run summary 生成：

```text
results/index.json
aggregates/leaderboard.json
aggregates/commit-history.json
aggregates/strategy-comparison.json
aggregates/runtime-quality.json
```

`optagent-dashboard` 应优先读取这些文件；进入单次运行详情时，再按 `summary_path` 读取 run summary 和 artifacts。

Dashboard 展示的是 promoted 长期事实，不是所有本地实验目录。进入 Dashboard 的文件范围固定为：

- `results/<group>/<strategy>/<yyyy>/<mm>/<run-id>.json`
- 可选的同名 artifact 目录：`metrics.json`、`solution.json`、`trace.json`
- `results/index.json`
- `aggregates/*.json`

CI 或本地 suite run 目录中的 `config.json`、`inventory.json`、`run_metadata.json`、`rows.jsonl`、`results.jsonl`、`results.csv`、`anytime.jsonl`、`curves.jsonl`、`throughput.jsonl`、`summary.json`、`report.md` 是单次运行审计证据。它们可以作为 CI artifact 或 `docs/evals/` 记录保存，但 Dashboard 不直接读取这些文件；需要通过发布步骤转换成 run summary。

错误也是事实。发布步骤必须保留 `status = "error"`、`feasible = false` 的 row，并写出 `error.type` / `error.message` 对应的 dashboard 字段，便于 Dashboard 区分“求解失败”“不可行”“质量回退”和“数据缺失”。

用于跨 commit 比较、默认策略选择或 release gate 的 Dashboard-worthy 结果应优先在 GitHub Actions 标准环境中产生：固定 Python / OS / wheel / benchmark commit / seed / tier / budget，并在 run summary 的 `environment` 中记录。维护者本地 smoke 可以验证记录链路和复现错误，但默认不作为质量趋势证据；确需 promoted 时，需要在 PR 或任务记录中说明环境和原因。

### 本地 Dashboard 联调

当需要修改 benchmark 输出字段、artifact 结构或 dashboard 展示逻辑时，不应等待一次完整 CI 成功 benchmark。可以使用本地联调链路把任意 suite run 目录转换成 dashboard 静态数据：

```bash
python scripts/sync_dashboard_local_data.py \
  docs/evals/benchmark-suite/runs/<timestamp> \
  --overwrite
```

该脚本会：

1. 读取 suite run 目录里的 `results.jsonl`。
2. 发布到本地隔离目录：

   ```text
   docs/evals/benchmark-suite/dashboard-local/
   ```

3. 生成 dashboard 需要的：

   ```text
   results/index.json
   aggregates/*.json
   results/<group>/<strategy>/<yyyy>/<mm>/<run-id>.json
   results/<group>/<strategy>/<yyyy>/<mm>/<run-id>/metrics.json
   ```

4. 同步到 sibling dashboard 仓库：

   ```text
   ../optagent-dashboard/public/data/
   ```

5. 写入 `../optagent-dashboard/public/data/LOCAL_DEV_DATA.md`，标记这份数据是本地联调用途。

然后启动 dashboard：

```bash
cd ../optagent-dashboard
npm run dev
```

这条链路适合联调：

- 新增或重命名 row 字段；
- 错误 row 在 Dashboard 的展示；
- `metrics.json`、`solution.json`、`trace.json` 等 artifact 的读取方式；
- aggregates 是否按预期分组、排序、筛选；
- Dashboard 页面文案、筛选和详情交互。

这条链路不表示数据已经 promoted。它会覆盖本地 dashboard 的 `public/data/results` 和 `public/data/aggregates`，但不会写入正式 `benchmarks/results` 或 `benchmarks/aggregates`。要恢复 dashboard 仓库中已提交的样例数据，使用 dashboard 仓库的版本控制恢复 `public/data`，或重新从 `optagent-benchmarks` 的正式 `results/` / `aggregates/` 同步。

#### 本地运行 GA / ALNS 非 MIP 全量联调

下面命令覆盖当前非 MIP benchmark families 的 smoke + calibration case，并只请求 GA / ALNS。调度 family 会额外写入 `cpsat` exact baseline row，这是 runner 的自动基线，不是用户请求的启发式策略。

```bash
python -m benchmarks.runners.run \
  --family interval_job_shop \
  --family cumulative_resource_scheduling \
  --family sequence_blackbox_tsp \
  --family sequence_quadratic_assignment \
  --tier smoke \
  --tier calibration \
  --strategy ga \
  --strategy alns \
  --max-iterations 5 \
  --time-limit-s 2 \
  --population-size 6 \
  --trace-limit 4 \
  --timestamp local-ga-alns-dashboard-$(date +%Y%m%d-%H%M%S)
```

同步到本地 dashboard：

```bash
python scripts/sync_dashboard_local_data.py \
  docs/evals/benchmark-suite/runs/<timestamp> \
  --overwrite \
  --runner local-ga-alns-dashboard
```

启动 dashboard：

```bash
cd ../optagent-dashboard
npm run dev
```

打开 `http://127.0.0.1:5173/`。如果 `public/data/LOCAL_DEV_DATA.md` 存在，页面会显示“本地联调数据”，提醒这不是 CI 可比历史。

如果本地 native / public route 失败，runner 仍会写出 `status = "error"` rows；这仍可用于联调 dashboard 的错误展示、筛选和 artifact 读取。质量比较结论应等待 GitHub Actions 标准环境产出的 promoted results。

旧的 run artifact dashboard 用于对比本地 `docs/evals/benchmark-suite/runs/<timestamp>/` 目录，不是长期事实层入口。

从已有 run artifact 生成 dashboard，不重新运行 benchmark：

```bash
python -m benchmarks.runners.dashboard \
  docs/evals/benchmark-suite/runs/<candidate> \
  --baseline-dir docs/evals/benchmark-suite/runs/<baseline> \
  --dashboard-id <stable-id>
```

默认输出目录：

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
python -m pytest -q \
  tests/test_benchmark_suite_catalog.py \
  tests/test_benchmark_telemetry.py
```

涉及 runner 行为、策略 row、输出 schema 或比较报告时，增加：

```bash
python -m pytest -q \
  tests/test_benchmark_suite_runner.py \
  tests/test_benchmark_suite_jsplib_runner.py \
  tests/test_benchmark_suite_rcpsp_runner.py \
  tests/test_benchmark_suite_qap_runner.py \
  tests/test_benchmark_suite_miplib_runner.py
```

涉及发布 wheel 的求解行为、公开 `solve(...)` 路线、trace 或 metadata 时，应在安装该 wheel 的环境中运行 focused tests 或 smoke benchmark，避免通过源码路径覆盖已安装包：

```bash
python -m pytest -q <focused-tests>
```

新增 case / family 时，最终报告必须写明：

- 修改了哪些 `definitions/`、`loaders/`、`models/`、`runners/` 文件。
- 是否只新增 case，还是改变了数据格式 / 建模方式 / 策略评测。
- 跑了哪些 focused tests。
- 是否验证了安装 wheel 后的 benchmark 命令。
