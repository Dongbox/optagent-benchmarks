# Presentation, Runner, And Dashboard Refactor Review

> Current runner note: benchmark execution is now centralized through root `run.py`
> and `BenchmarkCase.build_model() -> ModelBuilder`; case modules should not define
> new strategy declarations or series-level `solve_case()` entrypoints.

本文档评审 `presentation/` 是否适配当前 `cases/` 与 `presentation/` 的新结构，并定义后续重构需求。目标是保证 `presentation/` 中各个具体评测场景的结论都能被正常可视化，并按需发布到 dashboard 使用的数据层。

## Current Status

当前代码中已经形成两类 presentation 能力：

- `presentation/dashboard.py` 和 `presentation/compare.py`：直接读取标准 suite run directory 中的 `results.jsonl`，生成本地临时 markdown/json 报告。
- `presentation/publish_dashboard_results.py` 和 `presentation/generate_dashboard_data.py`：把标准 suite rows 发布为 `presentation/results/` 下的 immutable run summaries，再生成 `presentation/aggregates/*.json`。

这与新的 case 架构部分适配：

- 标准 suite runner 通过 `cases.registry` 调用具体实例模块，能产出 `results.jsonl` / `rows.jsonl`。
- `presentation.generate_dashboard_data --check` 当前能通过，说明已有 `presentation/results/` 与 `presentation/aggregates/` 在现有 contract 下自洽。
- `presentation.dashboard` 能读取标准 suite run directory 并生成临时可视化报告。

但它还没有完整适配“`presentation/` 下每个文件都是具体目标评测场景”的新边界。

## Findings

### P0: CI Dashboard Publication Entrypoint Is Stale

`.github/workflows/run-benchmarks.yml` 仍调用：

```bash
python -m benchmarks.presentation.publish_dashboard_results
PYTHONPATH=.. python -m benchmarks.presentation.generate_dashboard_data
```

但当前模块已经迁到：

```bash
python -m benchmarks.presentation.publish_dashboard_results
python -m benchmarks.presentation.generate_dashboard_data
```

`publish-results-index.yml` 同样监听和调用旧的 `presentation/generate_dashboard_data.py`。这会导致 CI dashboard 发布路径直接失败，也与 `presentation/` 作为展示与发布层的职责划分不一致。

### P0: Result Paths In Workflows Do Not Match `presentation/`

工作流仍检查、提交和监听顶层 `results` / `aggregates`：

```bash
git diff --quiet -- results aggregates
git add results aggregates
```

当前 contract 要求 dashboard evidence 位于：

```text
presentation/results/
presentation/aggregates/
```

这会导致 CI 即使成功生成新数据，也可能不会提交正确路径。

### P1: Publish Adapter Only Supports Standard Suite `results.jsonl`

`presentation/publish_dashboard_results.py` 只读取 run directory 下的 `results.jsonl`。这适合 `presentation/run.py` / `presentation/suite.py` 的标准 suite 场景，但不适合所有具体目标 runner。

已知缺口：

- `run_calibration_suite()` 的父目录写 `rows.jsonl`、`calibration_summary.json`、`strategy_feedback.json`，没有父级 `results.jsonl`。
- `presentation/phase6_internal_ga.py` 产出 `phase6_internal_ga_report.json` / `.md`，不是标准 result rows。
- 未来 ablation、multi-seed calibration、性能矩阵、策略对比 runner 可能产出场景级结论，而不是单 row 质量结果。

因此现在的 presentation publication 只覆盖“标准 suite 单次 row 发布”，没有“presentation 场景脚本 结论发布协议”。

### P1: Run Summary Identity Can Collide

`publish_dashboard_results._run_id()` 当前只使用：

```text
benchmark_group / strategy / benchmark_id / created_at / optagent_commit
```

它没有纳入这些会产生多行结果的维度：

- `model_style`
- `kind`
- `thread_count`
- `seed`
- `budget_profile`
- runner scenario id

当 suite 启用 TSP 多模型表达、parallel thread matrix、同 case 同 strategy 多 seed 或 exact/strategy 同时发布时，多个 rows 可能映射到同一个 `run_id` 和 summary path。`overwrite=False` 时会失败；`overwrite=True` 时会覆盖数据。

### P1: Dashboard Aggregates Do Not Use `compare_key` / `series_key`

`generate_dashboard_data.py` 当前按 `benchmark_group`、`benchmark_id`、`strategy`、`seed` 组织 history 和 comparison。新 case 架构已经引入：

- `compare_key`：跨策略比较粒度。
- `series_key`：趋势序列粒度。

但发布 summary 和 aggregates 没有保留和使用它们。这会让不同建模变体、问题表达方式或 runner 场景被混在同一条趋势里，削弱 dashboard 的比较语义。

### P1: Scenario Metadata Is Not Preserved In Published Summaries

标准 suite 已有：

- `runner_scenario_id`
- `runner_scenario_kind`
- `runner_scenario_description`
- `family_strategy_matrix`
- `budget_policy`
- `strategy_feedback`
- `parallel_matrix`

发布 summary 目前只保存基础 case/strategy/metrics/environment 字段，没有把 runner 场景身份、预算策略、矩阵维度、比较目的写入 dashboard-facing 数据。Dashboard 只能展示“某策略跑了某 case”，不能稳定表达“这是 CI smoke、calibration、多线程矩阵、策略候选比较还是内部 GA 对比”。

### P2: Benchmark Group Is Hard-Coded By Family

`publish_dashboard_results.FAMILY_GROUPS` 把 family 映射到 dashboard group。这个映射对现有标准 family 可用，但新架构下更合理的来源可能是：

- case declaration 中的 `source` / `problem_type` / `instance_type`
- runner scenario 自己声明的 dashboard group
- row 中显式携带的 `benchmark_group`

硬编码 family mapping 会让新增数据源、exact regression 子场景或横向评测场景需要修改 presentation 代码。

### P2: Publication Environment Uses Publish-Time Metadata

`_summary_from_row()` 的 `environment` 使用发布进程的 `sys.version` 和 `platform.platform()`。标准 suite 已经写出 `run_metadata.json` 和 `config["environment"]`，这些才是评测发生时的环境。对本地转发、CI artifact 二次发布或跨机器发布来说，publish-time environment 可能不等于 run-time environment。

### P2: Local Dashboard Reads Runner-Private Files Directly

`presentation/dashboard.py` 和 `presentation/compare.py` 直接读取 `results.jsonl`。这适合临时本地报告，但应明确为 “run workspace visualization”，不要与 dashboard static data contract 混淆。长期 dashboard 仍应只读 `presentation/results/index.json`、`presentation/aggregates/*.json` 和 run summaries。

## Target Architecture

目标分为三层：

1. `presentation/`：具体评测场景执行层。
   - 负责执行、生成 run workspace。
   - 可输出 row stream，也可输出 scenario report。

2. `presentation/`：发布与可视化适配层。
   - 提供 runner workspace 到 dashboard summaries 的 adapter。
   - 提供本地临时报告生成。
   - 提供 immutable summaries 到 static dashboard aggregates 的 generator。

3. `presentation/results` / `presentation/aggregates`：dashboard evidence layer。
   - 不依赖 runner 私有文件。
   - 保留 scenario、compare、series、budget、environment 等可解释维度。

## Required Design

### Runner Publication Manifest

每个可发布的 runner 场景应在 run directory 写出一个 manifest，例如：

```text
publication.json
```

建议字段：

```json
{
  "schema_version": 1,
  "runner_scenario_id": "standard_benchmark_suite",
  "runner_scenario_kind": "evaluation_scenario",
  "publication_kind": "row_summaries",
  "row_stream": "results.jsonl",
  "summary_file": "summary.json",
  "environment_file": "run_metadata.json",
  "dashboard_group_policy": "case_or_family",
  "publishable": true
}
```

非 row 型 runner 可以声明：

```json
{
  "publication_kind": "scenario_report",
  "report_file": "phase6_internal_ga_report.json",
  "dashboard_group": "internal-ga",
  "publishable": true
}
```

### Published Run Summary Extensions

在保持现有 required fields 兼容的基础上，summary 应扩展：

- `compare_key`
- `series_key`
- `model_style`
- `kind`
- `thread_count`
- `budget_profile`
- `effective_budget`
- `runner_scenario_id`
- `runner_scenario_kind`
- `runner_scenario_description`
- `publication_kind`
- `source_run_dir` 或 `source_run_id`

这些字段用于 dashboard 分组、筛选、趋势和回溯，不应只藏在 metrics 里。

### Stable Identity Rule

`run_id` 必须包含足够区分 row 的 identity dimensions。建议 identity hash 输入至少包含：

- `benchmark_group`
- `benchmark_id`
- `compare_key`
- `series_key`
- `strategy`
- `strategy_profile`
- `kind`
- `model_style`
- `seed`
- `thread_count`
- `budget_profile`
- `runner_scenario_id`
- `created_at`
- `optagent_commit`

文件名可以保持短 slug + hash，但 hash 输入必须完整。

### Aggregate Grouping Rule

Aggregates 应逐步改为：

- leaderboard：按 `benchmark_group` 和 strategy 聚合，但保留 scenario filter。
- commit-history：优先按 `series_key`、strategy、seed、runner scenario 聚合。
- strategy-comparison：优先按 `compare_key`、tier、model_style 或 series scope 聚合。
- runtime-quality：每个 point 携带 scenario、model_style、thread_count、budget_profile。

对于旧 summary 缺失新字段时，可回退到 `benchmark_id`。

### Adapter Registry

`presentation/` 应提供 adapter 层：

```text
presentation/
  publication.py
  adapters/
    standard_suite.py
    calibration_suite.py
    phase6_internal_ga.py
```

每个 adapter 负责把 runner workspace 转换为 dashboard-facing summary 或 scenario summary。`presentation/` 不反向导入 presentation。

## Phased Plan

### Phase A: Fix Broken Entrypoints

改动：

- 更新 `.github/workflows/run-benchmarks.yml` 调用 `benchmarks.presentation.publish_dashboard_results`。
- 更新 `.github/workflows/run-benchmarks.yml` 的提交路径为 `presentation/results` 和 `presentation/aggregates`。
- 更新 `.github/workflows/publish-results-index.yml` 的监听路径和命令为 `benchmarks.presentation.generate_dashboard_data`。
- 如需兼容旧命令，可新增短期 shim，但 shim 必须标注 deprecation。

验收：

- `python -m benchmarks.presentation.generate_dashboard_data --check` 通过。
- `python -m benchmarks.presentation.publish_dashboard_results --help` 可用。
- `python -m benchmarks.presentation.generate_dashboard_data` 不再出现在工作流和 docs 中，除非是显式 deprecation 文档。

### Phase B: Preserve New Case And Runner Dimensions

改动：

- `publish_dashboard_results` 从 row 中提取并写入 `compare_key`、`series_key`、`model_style`、`kind`、`thread_count`、`budget_profile`、`effective_budget`。
- `_run_id()` identity hash 纳入上述维度。
- `summary_path` 不再因同 case 同 strategy 多行而冲突。
- `presentation.suite` 在 rows 中补齐 `compare_key` / `series_key`，如果实例 row 已带则透传，否则从 case declaration 补齐。

验收：

- TSP 多 `--model-style` 发布不会冲突。
- `--parallel-matrix` 发布不会冲突。
- `presentation/results/index.json` 中 run entries 能看到 `model_style`、`kind`、`thread_count` 或可由 detail summary 获取。

### Phase C: Manifest-Based Publication

改动：

- 标准 suite run directory 写 `publication.json`。
- `publish_dashboard_results` 改名或抽出为 `presentation.publication.publish_run_workspace()`。
- 支持从 `rows.jsonl` 或 `results.jsonl` 发布标准 row summaries。
- 支持 calibration parent directory：读取 `rows.jsonl` + `calibration_summary.json`。

验收：

- 标准 suite、calibration suite 都能通过统一 publication API 生成 dashboard summaries。
- 没有 manifest 的目录仍可按 legacy standard suite fallback 发布，但给出 warning。

### Phase D: Scenario Report Dashboard Support

改动：

- 为 `phase6_internal_ga.py` 增加 publication manifest。
- 新增 scenario report summary schema，区分 `publication_kind = "scenario_report"`。
- `generate_dashboard_data` 新增 scenario index 或在现有 index 中标识 scenario report。
- Dashboard aggregates 至少能列出 scenario reports，并链接到 report summary。

验收：

- `phase6_internal_ga_report.json` 可发布到 `presentation/results/<scenario>/...`。
- Generated index 能保留该 report，且不会被 row leaderboard 当作普通 strategy run 误排序。

### Phase E: Aggregate Semantics Upgrade

改动：

- commit history 使用 `series_key` 优先。
- strategy comparison 使用 `compare_key` 优先。
- runtime-quality points 增加 scenario、model style、thread count、budget profile。
- dashboard-data contract 更新这些新增字段为 optional first，待历史数据迁移后再考虑 required。

验收：

- 旧历史 summaries 可继续生成 aggregates。
- 新 summaries 在 aggregates 中不会混淆 model variants 或 thread matrix rows。
- Error rows 仍保留在 index 和 aggregates 中。

## Validation Plan

基础验证：

```bash
python -m compileall presentation runners .github
python -m benchmarks.presentation.generate_dashboard_data --check
```

标准 suite 发布验证：

```bash
python -m benchmarks.presentation.suite \
  --family sequence_blackbox_tsp \
  --tier smoke \
  --case tsplib_berlin52 \
  --strategy local_search \
  --no-download \
  --timestamp presentation-standard-smoke

python -m benchmarks.presentation.publish_dashboard_results \
  ../docs/evals/benchmark-suite/runs/presentation-standard-smoke \
  --results-root /tmp/benchmark-presentation-results \
  --aggregates-root /tmp/benchmark-presentation-aggregates \
  --optagent-version 0.0.0 \
  --optagent-commit 0000000 \
  --optagent-commit-url https://example.invalid/optagent/commit/0000000 \
  --optagent-wheel-sha256 sha256:test \
  --benchmarks-commit 0000000 \
  --benchmarks-commit-url https://example.invalid/benchmarks/commit/0000000 \
  --created-at 2026-06-23T00:00:00Z
```

Collision 验证：

```bash
python -m benchmarks.presentation.suite \
  --family sequence_blackbox_tsp \
  --tier smoke \
  --case tsplib_berlin52 \
  --strategy local_search \
  --model-style sequence_var_external_call \
  --model-style sequence_transition_sum \
  --parallel-matrix \
  --thread-count 1 \
  --thread-count 2 \
  --no-download \
  --timestamp presentation-identity-smoke
```

验收要求：publication 不发生 path collision，生成 summaries 的 `run_id` 全部唯一。

## Non Goals

- 不让 dashboard 直接扫描 `docs/evals/**` 或 runner-private files。
- 不把 `presentation/results/` 历史数据作为测试重写对象，除非任务明确要求迁移历史。
- 不把 runner 场景逻辑搬进 presentation；presentation 只做发布和可视化适配。
- 不让 `presentation/` 重新承担 dashboard publication 的模块职责。
