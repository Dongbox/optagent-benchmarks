# PSPLIB

该数据源包含选定的 PSPLIB J90 资源约束项目调度实例。

每个 activity 具有时长、可再生资源需求和前置弧。模型约束前置关系和累计资源容量，并
最小化项目 makespan。

独立验证检查 activity 时间、全部前置弧、按时间展开的可再生资源容量，以及重新计算的
makespan。

```bash
./.venv/bin/python benchmark.py list-cases --family cumulative_resource_scheduling
```

原始 `.rcp` 放在 `rcpsp/raw/`；下载文件默认只是本地缓存，除非明确治理为 release
evidence。
