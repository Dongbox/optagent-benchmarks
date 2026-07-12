# Telemetry、指标与 Artifact

## 数据流

所有评测统计都从 OptAgent runtime 发布的 canonical telemetry 开始：

```text
OptAgent wheel
  -> canonical RunTelemetry
  -> benchmarks.telemetry_metrics
  -> normalized rows / curves / metrics
  -> benchmarks.telemetry_artifacts
  -> 不可变 artifact 目录
  -> optagent-dashboard
```

Runtime 负责事实，benchmark 负责指标推导和 artifact 发布，dashboard 只负责展示。

以下输入会被拒绝：

- 扁平 solution diagnostics；
- runner 私有 row；
- 求解器文本日志；
- dashboard summary；
- 已删除的历史 results/aggregates 数据。

缺失事实必须保留为 `unsupported`、`insufficient_data`、`error` 或 `null`，不得静默转成
零。

## 五维指标

### 有效性（Effectiveness）

最终可行性、目标值、相对/绝对 reference gap，以及标准化质量汇总。

### 效率（Efficiency）

Wall time、CPU time、迭代数、候选评估数、函数评估、吞吐率和内存。

### 稳健性（Robustness）

成功率、求解率、分布、方差、变异系数、分位数和最差标准化 gap。

### Anytime 表现

Incumbent curve、达到 target 的时间/评估次数、ECDF、primal integral、遗漏 target 惩罚和
trace 完整性。

### 统计有效性（Statistical Validity）

Matched Wilcoxon、Friedman、Vargha-Delaney A12、Cliff's Delta、多重比较修正，以及明确的
样本不足状态。

策略反馈只解释这些指标并给出保守的优化关注点，不会替用户选择策略，也不会修改运行时
配置。

## Artifact 契约

`publish-telemetry` 写出不可变目录：

```text
manifest.json
rows.jsonl
curves.jsonl
throughput.jsonl
five_dimensional_metrics.json
statistical_tests.json
strategy_optimization_feedback.json
dashboard.json
dashboard.md
```

`manifest.json` 是唯一入口，记录 schema、生成器版本、创建时间、commit、来源、每个文件的
SHA-256 和字节数。消费者必须先校验 manifest，再读取其他文件。

文件职责：

- `rows.jsonl`：每次运行的 canonical 事实；
- `curves.jsonl`：incumbent/checkpoint 曲线；
- `throughput.jsonl`：努力量和吞吐率；
- `five_dimensional_metrics.json`：benchmark 推导的五维指标；
- `statistical_tests.json`：配对和分组统计证据；
- `strategy_optimization_feedback.json`：优化信号、关注点和回退保护；
- `dashboard.json`：只含 presentation-ready 的物化结果。

Authority artifact 与 GA comparison artifact 属于不同证据类型，不能作为 telemetry dashboard
输入。

## CI 发布

CI 从 suite 工作区发布：

```bash
./.venv/bin/python benchmark.py publish-telemetry \
  --suite-run /path/to/suite-run \
  --output-dir artifacts/telemetry/RUN_ID \
  --optagent-commit OPTAGENT_SHA \
  --benchmarks-commit BENCHMARKS_SHA
```

每次运行使用新的 `RUN_ID`。`artifacts/telemetry/latest.json` 只负责指向最新不可变目录，
Dashboard 部署 workflow 根据该指针复制 artifact。

本地渲染：

```bash
./.venv/bin/python benchmark.py dashboard \
  artifacts/telemetry/RUN_ID \
  --output-root /tmp/dashboard
```

输出目录不得覆盖。
