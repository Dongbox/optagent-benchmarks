# JSPLIB

Job Shop 实例和 best-known solution 来自
[ScheduleOpt JSPLIB archive](https://scheduleopt.github.io/benchmarks/jsplib/)。

每个 job 是有序 operation 链，每个 operation 具有固定机器和时长。模型约束 job 前置关系
与机器 no-overlap，并最小化 makespan。

独立验证重建 operation interval，检查前置关系和机器容量，并在不信任求解器 summary 的
前提下重新计算 makespan。

```bash
./.venv/bin/python benchmark.py list-cases --family interval_job_shop
```

下载数据放在对应 `raw/` 目录，除非明确治理为 release evidence，否则只作为本地缓存。
