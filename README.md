# OptAgent Benchmarks

`optagent-benchmarks` 是独立维护的 OptAgent 评测仓库。评测人员使用已发布或指定的
OptAgent wheel，无需访问 OptAgent 源代码仓库。

本仓库负责 benchmark case、独立解验证、suite 执行、权威能力证据、GA 配对比较，
以及基于 canonical telemetry 的指标与 dashboard artifact。它不定义 OptAgent 的运行时
语义，也不实现求解器。

## 谁需要运行什么

开发人员日常并不需要执行全部命令。

| 命令 | 责任方 | 何时执行 |
| --- | --- | --- |
| `list-cases` | 开发人员手动 | 查找 case ID、family、tier。 |
| `run` | 开发人员手动 | 修改策略或 case 后做单实例快速诊断。 |
| `suite` | 开发人员按需；CI 自动 | 本地需要矩阵证据时手动运行；提交后的标准 smoke 由 CI 运行。 |
| `compare-ga` | GA 开发/评审人员手动；发布 CI 可自动 | 比较 baseline/challenger wheel，形成可审计的策略结论。 |
| `authority` | 发布负责人或发布 CI | 发布前验证完整能力矩阵；普通开发不运行完整 authority。 |
| `publish-telemetry` | CI 自动 | 从 suite 工作区发布不可变 telemetry artifact。开发人员只在排查指标时手动运行。 |
| `publish-review` | CI 自动 | 从 telemetry artifact 发布 Dashboard 使用的静态 review bundle。 |
| `dashboard` | CI 自动 | 校验并渲染 telemetry artifact。开发人员只在本地预览时手动运行。 |

推荐开发循环：

```text
修改策略/case
  -> run（开发人员手动）
  -> 必要时 suite（开发人员手动）
  -> push
  -> suite + publish-telemetry + publish-review（CI 自动）
  -> dashboard 部署（CI 自动）
```

GA 候选进入发布评审时再执行：

```text
compare-ga smoke
  -> compare-ga calibration
  -> compare-ga release holdout
  -> 审批后 promote
  -> authority release gate
```

## 环境准备

检出目录可以使用任意名称。所有命令都从仓库根目录执行：

```bash
git clone https://github.com/Dongbox/optagent-benchmarks.git optagent-benchmarks
cd optagent-benchmarks
python -m venv .venv
./.venv/bin/python -m pip install --upgrade pip pytest ruff
./.venv/bin/python -m pip install /path/to/optagent.whl
```

发布证据必须使用干净环境，不得安装 editable OptAgent 源码。只有本地源码联调时才设置：

```bash
export OPTAGENT_SOURCE_ROOT=/path/to/optagent
```

## 开发人员命令

### `list-cases`

只读取 registry，不执行求解器。输出为 JSON。

```bash
./.venv/bin/python benchmark.py list-cases

./.venv/bin/python benchmark.py list-cases \
  --family sequence_blackbox_tsp \
  --tier smoke
```

### `run`

用于单 case 快速诊断。标准输出中的 JSON 不是权威证据，也不能用于晋升策略基线。

```bash
./.venv/bin/python benchmark.py run \
  --case tsplib_berlin52 \
  --strategy ga \
  --model-style sequence_var_external_call \
  --seed 11 \
  --max-iterations 10 \
  --population-size 8 \
  --time-limit-s 0.5 \
  --no-download
```

需要对同一 case 比较多个策略或建模路径时，可重复传入 `--strategy` 或
`--model-style`。

### `suite`

用于生成可重复的 smoke、calibration 或线程矩阵工作区。默认输出到
`docs/evals/benchmark-suite/runs/`。普通策略修改通常由 CI 自动执行标准 smoke；只有
本地需要完整矩阵证据时才手动调用。

```bash
./.venv/bin/python benchmark.py suite \
  --family sequence_blackbox_tsp \
  --tier smoke \
  --strategy ga \
  --output-root /tmp/benchmark-runs \
  --timestamp local-ga-smoke
```

- 多 seed calibration：重复 `--calibration-seed`。
- 并发分析：使用 `--parallel-matrix`，或重复 `--thread-count`。
- 只检查将要运行的矩阵：使用 `--list-inventory`。

## GA 评审命令

### `compare-ga`

该命令只用于受控的 baseline/challenger GA 评测。

分别在隔离环境中运行两个 wheel：

```bash
./.venv/bin/python benchmark.py compare-ga run-pair \
  --protocol ga_release_smoke_v1 \
  --baseline-wheel /path/to/baseline.whl \
  --challenger-wheel /path/to/challenger.whl \
  --baseline-commit BASELINE_SHA \
  --challenger-commit CHALLENGER_SHA \
  --output-dir /tmp/ga-smoke
```

从已有不可变 run artifact 重新计算比较结果：

```bash
./.venv/bin/python benchmark.py compare-ga compare \
  --baseline /artifacts/baseline \
  --challenger /artifacts/challenger \
  --output-dir /tmp/ga-recomparison
```

只有 release holdout 得到 `improved` 且完成审批后才能晋升：

```bash
./.venv/bin/python benchmark.py compare-ga promote \
  --comparison-dir /artifacts/ga-holdout/comparison \
  --registry /artifact-storage/ga-baselines.json \
  --approved-by REVIEWER_ID
```

Smoke 只能发现无效证据或明显回退，不能产生 `improved` 晋升结论。完整规则见
[GA 策略比较](docs/ga-comparison.md)。

## 发布命令

### `authority`

完整 authority 由发布负责人或发布 CI 执行。它创建隔离环境、安装指定 wheel、运行冻结
矩阵、独立验证解，并写出带校验和的 rows 与 manifest。

提交前 smoke 只检查冻结计划，不生成权威结论：

```bash
./.venv/bin/python benchmark.py authority \
  --output-dir /tmp/authority-unused \
  --wheel /path/to/optagent.whl \
  --optagent-commit OPTAGENT_SHA \
  --plan-only
```

发布时执行完整 gate：

```bash
./.venv/bin/python benchmark.py authority \
  --output-dir /artifact-storage/authoritative-baseline \
  --wheel /path/to/optagent.whl \
  --optagent-commit OPTAGENT_SHA \
  --python-executable ./.venv/bin/python \
  --memory-limit-mb 4096 \
  --allow-download \
  --require-authoritative
```

`--require-authoritative` 在证据未通过 authority gate 时返回非零状态。完整规则见
[权威基线与能力声明](docs/authority.md)。

### `publish-telemetry`

CI 在 suite 完成后自动执行。它只接受 canonical telemetry JSON，或通过 `--suite-run`
读取 suite 工作区中嵌入的 canonical telemetry；输出目录不可覆盖。

CI 使用方式：

```bash
./.venv/bin/python benchmark.py publish-telemetry \
  --suite-run /artifact-storage/runs/gha-smoke \
  --output-dir /artifact-storage/telemetry/gha-smoke \
  --optagent-commit OPTAGENT_SHA \
  --benchmarks-commit BENCHMARKS_SHA
```

本地排查单独 telemetry 文件：

```bash
./.venv/bin/python benchmark.py publish-telemetry \
  /path/to/run-a-telemetry.json \
  /path/to/run-b-telemetry.json \
  --output-dir /tmp/telemetry-artifact \
  --reference tsplib_berlin52=7542 \
  --target tsplib_berlin52=7600
```

产物包括 `manifest.json`、`rows.jsonl`、`curves.jsonl`、五维指标、统计证据、策略反馈和
`dashboard.json`。详细契约见 [Telemetry、指标与 Artifact](docs/telemetry-artifacts.md)。

### `publish-review`

发布 Dashboard 直接消费的静态策略评审 bundle。单策略结果始终可用；提供兼容的 baseline
telemetry artifact 时，会额外发布 factual comparison，不包含 verdict、promotable 或综合分。

```bash
./.venv/bin/python benchmark.py publish-review \
  --current-artifact /artifacts/telemetry/current \
  --baseline-artifact /artifacts/telemetry/approved-baseline \
  --output-dir /artifacts/reviews/current \
  --protocol-id ga_calibration_v1
```

省略 `--baseline-artifact` 时，bundle 会记录 `baseline_not_packaged`，Dashboard 的基线比较
模式只显示缺失原因。

### `dashboard`

CI 自动校验并渲染已发布的 telemetry artifact，不从 suite row、日志或历史结果重新计算
指标。开发人员只有在本地预览 artifact 时才需要手动运行。

```bash
./.venv/bin/python benchmark.py dashboard \
  /tmp/telemetry-artifact \
  --output-root /tmp/telemetry-dashboard \
  --dashboard-id local-preview
```

查看完整参数：

```bash
./.venv/bin/python benchmark.py --help
./.venv/bin/python benchmark.py <command> --help
```

## 开发验证

```bash
./.venv/bin/python -m pytest -q
./.venv/bin/ruff check benchmark.py benchmarks tests
./.venv/bin/python -m compileall benchmark.py benchmarks tests
./.venv/bin/python benchmark.py list-cases --tier smoke
```

修改 case 后，至少再运行一个受影响 family 的小型 `--no-download` case。生成的工作区和
下载缓存不是文档，不应提交；只有 CI 发布的不可变 telemetry artifact 可以进入
`artifacts/telemetry/`。

## 仓库结构

```text
benchmark.py        唯一命令入口
benchmarks/         实现、cases、独立验证与 presentation
artifacts/telemetry CI 发布的不可变 telemetry artifact 与 latest 指针
docs/               评测政策和数据契约
tests/              命令、artifact、指标和 case 回归测试
```
