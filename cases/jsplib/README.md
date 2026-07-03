# JSPLIB 数据来源说明

JSPLIB 目录保存来自 ScheduleOpt 归档的 job-shop benchmark case，当前是作业车间调度问题。数据集来源：

- 文档页：https://scheduleopt.github.io/benchmarks/jsplib/
- 实例数据：https://github.com/ScheduleOpt/benchmarks/tree/main/jobshop/instances/json
- 参考解：https://github.com/ScheduleOpt/benchmarks/blob/main/jobshop/solutions/bks.json

## 相关 case

### smoke

- `jsplib_ft06`
  - 问题描述：6 个作业、6 台机器的 job-shop 调度问题。
  - 规模：`jobs=6`，`machines=6`，`ops=36`
  - 参考值：`objective=55`
  - 类型：`toy`
- `jsplib_ft10`
  - 问题描述：10 个作业、10 台机器的 job-shop 调度问题。
  - 规模：`jobs=10`，`machines=10`，`ops=100`
  - 参考值：`objective=930`
  - 类型：`toy`
- `jsplib_ft20`
  - 问题描述：20 个作业、5 台机器的 job-shop 调度问题。
  - 规模：`jobs=20`，`machines=5`，`ops=100`
  - 参考值：`objective=1165`
  - 类型：`toy`
- `jsplib_la01`
  - 问题描述：10 个作业、5 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`jobs=10`，`machines=5`，`ops=50`
  - 参考值：`objective=666`
  - 类型：`toy`

### calibration

- `jsplib_abz5`
  - 问题描述：10 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`jobs=10`，`machines=10`，`ops=100`
  - 参考值：`objective=1234`
  - 类型：`toy`
- `jsplib_abz6`
  - 问题描述：10 个作业、10 台机器的 job-shop 调度问题。
  - 规模：`jobs=10`，`machines=10`，`ops=100`
  - 参考值：`objective=943`
  - 类型：`toy`
- `jsplib_la16`
  - 问题描述：10 个作业、10 台机器的 job-shop 调度问题。
  - 规模：`jobs=10`，`machines=10`，`ops=100`
  - 参考值：`objective=945`
  - 类型：`toy`
- `jsplib_la21`
  - 问题描述：15 个作业、10 台机器的 job-shop 调度问题。
  - 规模：`jobs=15`，`machines=10`，`ops=150`
  - 参考值：`objective=1046`
  - 类型：`toy`
- `jsplib_orb03`
  - 问题描述：10 个作业、10 台机器的 job-shop 调度问题。
  - 规模：`jobs=10`，`machines=10`，`ops=100`
  - 参考值：`objective=1005`
  - 类型：`toy`
- `jsplib_orb04`
  - 问题描述：10 个作业、10 台机器的 job-shop 调度问题。
  - 规模：`jobs=10`，`machines=10`，`ops=100`
  - 参考值：`objective=1005`
  - 类型：`toy`

### full

- `jsplib_abz7`
  - 问题描述：20 个作业、15 台机器的 job-shop 调度问题。
  - 规模：`jobs=20`，`machines=15`，`ops=300`
  - 参考值：`objective=656`
  - 类型：`easy`
- `jsplib_dmu01`
  - 问题描述：20 个作业、15 台机器的 job-shop 调度问题。
  - 规模：`jobs=20`，`machines=15`，`ops=300`
  - 参考值：`objective=2563`
  - 类型：`medium`
- `jsplib_dmu06`
  - 问题描述：20 个作业、20 台机器的 job-shop 调度问题。
  - 规模：`jobs=20`，`machines=20`，`ops=400`
  - 参考值：`objective=3244`
  - 类型：`hard`
- `jsplib_dmu41`
  - 问题描述：20 个作业、15 台机器的 job-shop 调度问题。
  - 规模：`jobs=20`，`machines=15`，`ops=300`
  - 参考值：`upper_bound=3248`，`lower_bound=3176`
  - 类型：`open`
- `jsplib_dmu46`
  - 问题描述：20 个作业、20 台机器的 job-shop 调度问题。
  - 规模：`jobs=20`，`machines=20`，`ops=400`
  - 参考值：`upper_bound=4035`，`lower_bound=3780`
  - 类型：`open`
- `jsplib_dmu51`
  - 问题描述：30 个作业、15 台机器的 job-shop 调度问题。
  - 规模：`jobs=30`，`machines=15`，`ops=450`
  - 参考值：`upper_bound=4151`，`lower_bound=4070`
  - 类型：`open`
- `jsplib_la31`
  - 问题描述：30 个作业、10 台机器的 job-shop 调度问题。
  - 规模：`jobs=30`，`machines=10`，`ops=300`
  - 参考值：`objective=1784`
  - 类型：`toy`
- `jsplib_la36`
  - 问题描述：15 个作业、15 台机器的 job-shop 调度问题。
  - 规模：`jobs=15`，`machines=15`，`ops=225`
  - 参考值：`objective=1268`
  - 类型：`toy`
- `jsplib_swv01`
  - 问题描述：20 个作业、10 台机器的 job-shop 调度问题。
  - 规模：`jobs=20`，`machines=10`，`ops=200`
  - 参考值：`objective=1407`
  - 类型：`toy`
- `jsplib_swv06`
  - 问题描述：20 个作业、15 台机器的 job-shop 调度问题。
  - 规模：`jobs=20`，`machines=15`，`ops=300`
  - 参考值：`objective=1667`
  - 类型：`hard`
- `jsplib_ta11js`
  - 问题描述：20 个作业、15 台机器的 job-shop 调度问题。
  - 规模：`jobs=20`，`machines=15`，`ops=300`
  - 参考值：`objective=1357`
  - 类型：`medium`
- `jsplib_ta21js`
  - 问题描述：20 个作业、20 台机器的 job-shop 调度问题。
  - 规模：`jobs=20`，`machines=20`，`ops=400`
  - 参考值：`objective=1642`
  - 类型：`medium`
- `jsplib_ta31js`
  - 问题描述：30 个作业、15 台机器的 job-shop 调度问题。
  - 规模：`jobs=30`，`machines=15`，`ops=450`
  - 参考值：`objective=1764`
  - 类型：`easy`
- `jsplib_yn1`
  - 问题描述：20 个作业、20 台机器的 job-shop 调度问题。
  - 规模：`jobs=20`，`machines=20`，`ops=400`
  - 参考值：`objective=884`
  - 类型：`hard`

### pressure

- `jsplib_dmu16`
  - 问题描述：30 个作业、20 台机器的 job-shop 调度问题。
  - 规模：`jobs=30`，`machines=20`，`ops=600`
  - 参考值：`upper_bound=3750`，`lower_bound=3734`
  - 类型：`open`
- `jsplib_dmu56`
  - 问题描述：30 个作业、20 台机器的 job-shop 调度问题。
  - 规模：`jobs=30`，`machines=20`，`ops=600`
  - 参考值：`upper_bound=4934`，`lower_bound=4755`
  - 类型：`open`
- `jsplib_swv11`
  - 问题描述：50 个作业、10 台机器的 job-shop 调度问题。
  - 规模：`jobs=50`，`machines=10`，`ops=500`
  - 参考值：`objective=2983`
  - 类型：`medium`
- `jsplib_swv16`
  - 问题描述：50 个作业、10 台机器的 job-shop 调度问题。
  - 规模：`jobs=50`，`machines=10`，`ops=500`
  - 参考值：`objective=2924`
  - 类型：`toy`
- `jsplib_ta41js`
  - 问题描述：30 个作业、20 台机器的 job-shop 调度问题。
  - 规模：`jobs=30`，`machines=20`，`ops=600`
  - 参考值：`upper_bound=2005`，`lower_bound=1926`
  - 类型：`open`
- `jsplib_ta51js`
  - 问题描述：50 个作业、15 台机器的 job-shop 调度问题。
  - 规模：`jobs=50`，`machines=15`，`ops=750`
  - 参考值：`objective=2760`
  - 类型：`toy`

## 问题定义

每个 case 都是在满足作业工序先后约束和机器不重叠约束的前提下，最小化项目完工时间。
