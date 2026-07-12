# FJSPLIB

Flexible Job Shop 实例来自
[SchedulingLab FJSP archive](https://github.com/SchedulingLab/fjsp-instances)。

## 本地数据

- 原始 `.txt` 和标准化 `.json` 证据位于 `fjobshop/raw/`；
- 离线运行以标准化 JSON 为 loader 契约；
- JSON 记录机器数、jobs、operations、候选机器、加工时间和 reference 来源；
- `reference.kind=optimum` 表示已闭合最优值，`bounds` 表示受治理的上下界或 best-known。

## 模型与验证

每个 operation 为候选机器创建 optional interval，使用 presence 和 `exactly_one` 选择机器。
选中 interval 的 start/end projection 定义工序前置关系；每台机器使用 sequence/no-overlap
约束避免重叠，目标最小化 makespan。

独立验证检查每个 operation 恰好选择一个机器、工序前置、机器不重叠和重新计算的
makespan。

```bash
./.venv/bin/python benchmark.py list-cases --family flexible_interval_job_shop
```
