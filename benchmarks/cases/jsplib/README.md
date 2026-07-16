# JSPLIB

## 数据来源说明

JSPLIB（Job-Shop Scheduling Problem Library）是 job-shop 调度问题基准集，提供固定机器路线、加工时间和参考值。

数据集来源网站：

- JSPLIB 说明页：https://scheduleopt.github.io/benchmarks/jsplib/
- 实例数据：https://github.com/ScheduleOpt/benchmarks/tree/main/jobshop/instances/json
- 参考解：https://github.com/ScheduleOpt/benchmarks/blob/main/jobshop/solutions/bks.json
- 本地实例目录：`benchmarks/cases/jsplib/jobshop/raw/`

## 问题说明

给定多个作业、多个机器以及每个作业的固定机器访问顺序和加工时间，在不违反机器不重叠和工序先后约束的前提下最小化 makespan。

## 数据筛选依据

规模定义：operations = jobs × machines，是 JSPLIB tier 分层的唯一规模指标。

- `jobs`：作业数量；
- `machines`：机器数量；
- `operations`：总工序数，固定为 `jobs × machines`；
- 核心规模指标为 operations，同时结合 jobs 和 machines判断调度资源规模。

tier 分类范围：

- smoke：operations=36-100
- calibration：operations=100-150
- full：operations=200-450
- pressure：operations=500-750
筛选策略：以 operations 递增为主线，结合实例系列、参考解状态和难度标签选择代表性 case。

## 建模说明

建模方式：使用 interval variables 表示工序时间区间，使用 machine sequence/no-overlap 约束保证机器不重叠，使用 precedence 约束保证工序顺序，目标为最小化 makespan。

适用的求解方式：

- `solve()`：适用；
- `solve_cpsat()`：适用；
- `solve_milp()`：当前不适用，未提供 interval/sequence 模型到 MILP 的 lowering。

## 特殊备注

- `operations` 按 `jobs × machines` 计算。
- 大多参考值为公开最优值；部分 dmu 和 ta41js 使用公开上下界区间。

## 相关 case

### smoke

- `jsplib_ft06`
  - 问题描述：6 个作业、6 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=36`
  - 参考值性质：最优
  - 参考值/区间：`objective=55`
  - 备注：`toy`

- `jsplib_ft10`
  - 问题描述：10 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=100`
  - 参考值性质：最优
  - 参考值/区间：`objective=930`
  - 备注：`toy`

- `jsplib_ft20`
  - 问题描述：20 个作业、5 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=100`
  - 参考值性质：最优
  - 参考值/区间：`objective=1165`
  - 备注：`toy`

- `jsplib_la01`
  - 问题描述：10 个作业、5 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=50`
  - 参考值性质：最优
  - 参考值/区间：`objective=666`
  - 备注：`toy`

### calibration

- `jsplib_abz5`
  - 问题描述：10 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=100`
  - 参考值性质：最优
  - 参考值/区间：`objective=1234`
  - 备注：`toy`

- `jsplib_abz6`
  - 问题描述：10 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=100`
  - 参考值性质：最优
  - 参考值/区间：`objective=943`
  - 备注：`toy`

- `jsplib_la16`
  - 问题描述：10 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=100`
  - 参考值性质：最优
  - 参考值/区间：`objective=945`
  - 备注：`toy`

- `jsplib_la21`
  - 问题描述：15 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=150`
  - 参考值性质：最优
  - 参考值/区间：`objective=1046`
  - 备注：`toy`

- `jsplib_orb03`
  - 问题描述：10 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=100`
  - 参考值性质：最优
  - 参考值/区间：`objective=1005`
  - 备注：`toy`

- `jsplib_orb04`
  - 问题描述：10 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=100`
  - 参考值性质：最优
  - 参考值/区间：`objective=1005`
  - 备注：`toy`

### full

- `jsplib_abz7`
  - 问题描述：20 个作业、15 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=300`
  - 参考值性质：最优
  - 参考值/区间：`objective=656`
  - 备注：`easy`

- `jsplib_la31`
  - 问题描述：30 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=300`
  - 参考值性质：最优
  - 参考值/区间：`objective=1784`
  - 备注：`toy`

- `jsplib_la36`
  - 问题描述：15 个作业、15 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=225`
  - 参考值性质：最优
  - 参考值/区间：`objective=1268`
  - 备注：`toy`

- `jsplib_dmu01`
  - 问题描述：20 个作业、15 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=300`
  - 参考值性质：最优
  - 参考值/区间：`objective=2563`
  - 备注：`medium`

- `jsplib_dmu06`
  - 问题描述：20 个作业、20 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=400`
  - 参考值性质：最优
  - 参考值/区间：`objective=3244`
  - 备注：`hard`

- `jsplib_dmu41`
  - 问题描述：20 个作业、15 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=300`
  - 参考值性质：可行（最好已知上界）
  - 参考值/区间：`lower_bound=3176`，`upper_bound=3248`
  - 备注：`open`

- `jsplib_dmu46`
  - 问题描述：20 个作业、20 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=400`
  - 参考值性质：可行（最好已知上界）
  - 参考值/区间：`lower_bound=3780`，`upper_bound=4035`
  - 备注：`open`

- `jsplib_dmu51`
  - 问题描述：30 个作业、15 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=450`
  - 参考值性质：可行（最好已知上界）
  - 参考值/区间：`lower_bound=4070`，`upper_bound=4151`
  - 备注：`open`

- `jsplib_swv01`
  - 问题描述：20 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=200`
  - 参考值性质：最优
  - 参考值/区间：`objective=1407`
  - 备注：`toy`

- `jsplib_swv06`
  - 问题描述：20 个作业、15 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=300`
  - 参考值性质：最优
  - 参考值/区间：`objective=1667`
  - 备注：`hard`

- `jsplib_ta11js`
  - 问题描述：20 个作业、15 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=300`
  - 参考值性质：最优
  - 参考值/区间：`objective=1357`
  - 备注：`medium`

- `jsplib_ta21js`
  - 问题描述：20 个作业、20 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=400`
  - 参考值性质：最优
  - 参考值/区间：`objective=1642`
  - 备注：`medium`

- `jsplib_ta31js`
  - 问题描述：30 个作业、15 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=450`
  - 参考值性质：最优
  - 参考值/区间：`objective=1764`
  - 备注：`easy`

- `jsplib_yn1`
  - 问题描述：20 个作业、20 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=400`
  - 参考值性质：最优
  - 参考值/区间：`objective=884`
  - 备注：`hard`

### pressure

- `jsplib_dmu16`
  - 问题描述：30 个作业、20 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=600`
  - 参考值性质：可行（最好已知上界）
  - 参考值/区间：`lower_bound=3734`，`upper_bound=3750`
  - 备注：`open`

- `jsplib_dmu56`
  - 问题描述：30 个作业、20 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=600`
  - 参考值性质：可行（最好已知上界）
  - 参考值/区间：`lower_bound=4755`，`upper_bound=4934`
  - 备注：`open`

- `jsplib_swv11`
  - 问题描述：50 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=500`
  - 参考值性质：最优
  - 参考值/区间：`objective=2983`
  - 备注：`medium`

- `jsplib_swv16`
  - 问题描述：50 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=500`
  - 参考值性质：最优
  - 参考值/区间：`objective=2924`
  - 备注：`toy`

- `jsplib_ta41js`
  - 问题描述：30 个作业、20 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=600`
  - 参考值性质：可行（最好已知上界）
  - 参考值/区间：`lower_bound=1926`，`upper_bound=2005`
  - 备注：`open`

- `jsplib_ta51js`
  - 问题描述：50 个作业、15 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=750`
  - 参考值性质：最优
  - 参考值/区间：`objective=2760`
  - 备注：`toy`
