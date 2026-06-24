# JSPLIB 数据来源说明

JSPLIB 目录保存来自 ScheduleOpt 归档的 job-shop benchmark case，当前是作业车间调度问题。

## 相关 case

- `jsplib_abz5`
  - 问题描述：10 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`jobs=10`，`machines=10`
  - 参考值：`objective=1234`
- `jsplib_abz7`
  - 问题描述：20 个作业、15 台机器的 job-shop 调度问题。
  - 规模：`jobs=20`，`machines=15`
  - 参考值：`objective=656`
- `jsplib_dmu01`
  - 问题描述：20 个作业、15 台机器的 job-shop 调度问题。
  - 规模：`jobs=20`，`machines=15`
  - 参考值：`objective=2563`
- `jsplib_ft06`
  - 问题描述：6 个作业、6 台机器的 job-shop 调度问题。
  - 规模：`jobs=6`，`machines=6`
  - 参考值：`objective=55`
- `jsplib_ft10`
  - 问题描述：10 个作业、10 台机器的 job-shop 调度问题。
  - 规模：`jobs=10`，`machines=10`
  - 参考值：`objective=930`
- `jsplib_la16`
  - 问题描述：10 个作业、10 台机器的 job-shop 调度问题。
  - 规模：`jobs=10`，`machines=10`
  - 参考值：`objective=945`
- `jsplib_la21`
  - 问题描述：15 个作业、10 台机器的 job-shop 调度问题。
  - 规模：`jobs=15`，`machines=10`
  - 参考值：`objective=1046`
- `jsplib_swv01`
  - 问题描述：20 个作业、10 台机器的 job-shop 调度问题。
  - 规模：`jobs=20`，`machines=10`
  - 参考值：`objective=1407`

## 问题定义

每个 case 都是在满足作业工序先后约束和机器不重叠约束的前提下，最小化项目完工时间。
