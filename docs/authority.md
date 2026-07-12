# 权威基线与能力声明

## 目的

Authority baseline 用于回答“指定 OptAgent wheel 在冻结矩阵上具备哪些原生求解能力”。它
不是开发 smoke，也不是策略调参工具。

权威证据必须同时绑定：

- OptAgent wheel SHA-256 与构建 commit；
- benchmark commit；
- Python、平台、CPU 和 backend 版本；
- 冻结 case/strategy/model-style/seed/thread 矩阵；
- 每个 case 的 reference 与原始实例校验和；
- 独立 solution verification 结果；
- 完整 rows 与 manifest 校验和。

## 原生能力口径

HiGHS 随 OptAgent wheel 一同交付，用户无需安装第三方 solver，因此 `embedded_highs` 属于
OptAgent 原生能力。需要用户额外安装的 backend 只能算兼容、适配或 extra，不能进入原生
能力声明。

Native search 只有在对应 case 通过独立验证时才能声明支持。某个策略失败不自动否定整个
problem family；family 支持与 strategy profile 结果分别记录。

## 权威条件

以下任一情况都会使 artifact 变为 `non_authoritative`：

- benchmark 工作树不干净；
- wheel、commit 或 backend 身份缺失；
- 冻结坐标缺失或重复；
- 运行失败、超时或未通过独立解验证；
- reference/instance 证据缺少校验和；
- 发生未声明 fallback；
- 输出目录不是空目录。

## 计划预检

开发和 CI smoke 可以验证冻结矩阵，但不得生成权威结论：

```bash
./.venv/bin/python benchmark.py authority \
  --output-dir /tmp/unused \
  --wheel /path/to/optagent.whl \
  --optagent-commit OPTAGENT_SHA \
  --plan-only
```

输出中的 `authoritative` 固定为 `false`。该模式不会创建隔离环境，也不会执行求解。

## 完整发布 Gate

只有发布负责人或发布 CI 执行：

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

该命令为 wheel 创建隔离环境，按冻结顺序执行全部坐标，写出 `rows.jsonl` 和
`manifest.json`。`--require-authoritative` 在最终状态不是 `authoritative` 时返回非零退出码。

发布声明只能引用已归档 artifact 的 manifest 和 checksum，不能引用本地控制台输出。
