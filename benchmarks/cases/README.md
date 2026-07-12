# Benchmark Cases

`benchmarks/cases/` 负责 case 声明、数据加载、reference、模型构建、解码和独立解验证。

## 数据集

- [TSPLIB](tsplib/README.md)：对称 TSP 与 sequence 建模变体
- [QAPLIB](qaplib/README.md)：二次指派
- [JSPLIB](jsplib/README.md)：Job Shop
- [FJSPLIB](fjsplib/README.md)：Flexible Job Shop
- [PSPLIB](psplib/README.md)：资源约束项目调度
- [MIPLIB 2017](miplib2017/README.md)：精确 Linear MIP
- [Custom](custom/README.md)：benchmark 自有业务 case

## 查询 Inventory

Markdown 不维护完整 case 列表。Registry 是 case ID、family、tier、model style、生命周期、
规模、reference 和数据路径的唯一事实来源：

```bash
./.venv/bin/python benchmark.py list-cases
```

## 目录结构

```text
benchmarks/cases/<source>/<problem>/
  __init__.py   同来源聚合
  _domain.py    解析、建模和验证公共逻辑
  <case>.py     case 声明
  raw/          受治理的源文件或本地下载缓存
```

## 维护规则

- ID 使用小写 source 前缀，例如 `tsplib_berlin52`。
- Reference 必须记录来源，并说明是 optimum、bound 还是 best-known。
- 独立验证不得信任求解器报告的 feasibility 或 objective。
- 禁止按 benchmark ID 写策略特例或 case-specific tuning。
- 新 release-gate case 必须有稳定本地数据和证据校验和。
- Raw cache 只有在许可证和离线 release gate 明确允许时才能提交。
