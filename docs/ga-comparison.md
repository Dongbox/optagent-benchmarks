# GA 策略比较

## 目的

GA comparison 用于判断一次 GA 策略修改相对冻结 baseline 是改进、回退、无明显变化，还是
证据无效。它不是自动 tuner，也不会为单个建模问题学习参数。

比较对象必须是两个明确的 OptAgent wheel。Baseline 与 challenger 在独立环境中运行相同
case、model style、seed、预算和线程数，执行顺序交错，避免系统漂移偏向某一方。

## 三阶段协议

| 协议 | 用途 | 可产生 `improved` |
| --- | --- | --- |
| `ga_release_smoke_v1` | 发现无效证据和明显回退 | 否 |
| `ga_calibration_v1` | 在 calibration case 上检查方向和稳定性 | 否 |
| `ga_release_holdout_v1` | 冻结 holdout 发布判断 | 是 |

不能根据 smoke 或 calibration 结果晋升 baseline。Calibration 期间确定阈值和配置后，进入
holdout 前必须冻结；不得根据 holdout 结果反复调参数。

## Delta Index

综合指数包含：

- 质量 40%；
- Anytime 30%；
- 稳健性 20%；
- 效率 10%。

综合分只是排序反馈，不能覆盖 validity gate。只要存在解验证失败、坐标不匹配、telemetry
缺失、trace 不完整、预算不一致或显著质量回退，结论就不能是 `improved`。

统计证据使用 matched samples，并报告置信区间、Wilcoxon、效应量和样本不足状态。样本
不足不会被解释为“没有差异”。

## 运行配对评测

```bash
./.venv/bin/python benchmark.py compare-ga run-pair \
  --protocol ga_release_smoke_v1 \
  --baseline-wheel /path/to/baseline.whl \
  --challenger-wheel /path/to/challenger.whl \
  --baseline-commit BASELINE_SHA \
  --challenger-commit CHALLENGER_SHA \
  --output-dir /tmp/ga-smoke
```

输出目录必须为空。结果结构：

```text
baseline/                 baseline 不可变 run artifact
challenger/               challenger 不可变 run artifact
comparison/
  comparison_manifest.json
  paired_rows.jsonl
  dimension_metrics.json
  delta_index.json
  statistical_evidence.json
  feedback.md
execution_plan.json
```

## 重新比较已有 Artifact

```bash
./.venv/bin/python benchmark.py compare-ga compare \
  --baseline /artifacts/baseline \
  --challenger /artifacts/challenger \
  --output-dir /tmp/recomparison
```

该动作不会重新求解，只验证 artifact 并重新计算比较输出。

## 晋升 Baseline

只有 holdout verdict 为 `improved`、所有 gate 通过并完成显式审批后才允许：

```bash
./.venv/bin/python benchmark.py compare-ga promote \
  --comparison-dir /artifacts/holdout/comparison \
  --registry /artifact-storage/ga-baselines.json \
  --approved-by REVIEWER_ID
```

晋升是治理动作，不由普通开发 CI 自动执行。
