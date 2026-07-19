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

| tier | case 数量 | operations 范围 |
|---|---:|---:|
| smoke | 20 | 30–100 |
| calibration | 20 | 101–199 |
| full | 15 | 200–499 |
| pressure | 10 | 500–750 |

筛选策略：每个算例使用 operations 与 jobs/machines 比例、加工时间分布、作业和机器负荷不均衡、机器路线重合度、机器先后关系图的密度与熵构成特征向量。在同一 tier 候选集内对各特征做 z-score 标准化；两个算例的近似程度为标准化特征向量之间的欧氏距离，距离越小表示结构和数据特征越接近。

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

- `jsplib_la01`
  - 问题描述：10 个作业、5 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=50`
  - 参考值性质：最优
  - 参考值/区间：`objective=666`
  - 备注：`toy`

- `jsplib_la02`
  - 问题描述：10 个作业、5 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=50`
  - 参考值性质：最优
  - 参考值/区间：`objective=655`
  - 备注：未标注

- `jsplib_la03`
  - 问题描述：10 个作业、5 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=50`
  - 参考值性质：最优
  - 参考值/区间：`objective=597`
  - 备注：未标注

- `jsplib_la04`
  - 问题描述：10 个作业、5 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=50`
  - 参考值性质：最优
  - 参考值/区间：`objective=590`
  - 备注：未标注

- `jsplib_la05`
  - 问题描述：10 个作业、5 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=50`
  - 参考值性质：最优
  - 参考值/区间：`objective=593`
  - 备注：未标注

- `jsplib_la09`
  - 问题描述：15 个作业、5 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=75`
  - 参考值性质：最优
  - 参考值/区间：`objective=951`
  - 备注：未标注

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

- `jsplib_la11`
  - 问题描述：20 个作业、5 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=100`
  - 参考值性质：最优
  - 参考值/区间：`objective=1222`
  - 备注：未标注

- `jsplib_la12`
  - 问题描述：20 个作业、5 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=100`
  - 参考值性质：最优
  - 参考值/区间：`objective=1039`
  - 备注：未标注

- `jsplib_la14`
  - 问题描述：20 个作业、5 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=100`
  - 参考值性质：最优
  - 参考值/区间：`objective=1292`
  - 备注：未标注

- `jsplib_la17`
  - 问题描述：10 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=100`
  - 参考值性质：最优
  - 参考值/区间：`objective=784`
  - 备注：未标注

- `jsplib_orb07`
  - 问题描述：10 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=100`
  - 参考值性质：最优
  - 参考值/区间：`objective=397`
  - 备注：未标注

- `jsplib_orb08`
  - 问题描述：10 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=100`
  - 参考值性质：最优
  - 参考值/区间：`objective=899`
  - 备注：未标注

- `jsplib_orb10`
  - 问题描述：10 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=100`
  - 参考值性质：最优
  - 参考值/区间：`objective=944`
  - 备注：未标注

- `jsplib_tai_10_10_1`
  - 问题描述：10 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=100`
  - 参考值性质：最优
  - 参考值/区间：`objective=8219`
  - 备注：未标注

- `jsplib_tai_10_10_2`
  - 问题描述：10 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=100`
  - 参考值性质：最优
  - 参考值/区间：`objective=7416`
  - 备注：未标注

- `jsplib_tai_10_10_4`
  - 问题描述：10 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=100`
  - 参考值性质：最优
  - 参考值/区间：`objective=8657`
  - 备注：未标注

- `jsplib_tai_10_10_5`
  - 问题描述：10 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=100`
  - 参考值性质：最优
  - 参考值/区间：`objective=7936`
  - 备注：未标注

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

- `jsplib_la13`
  - 问题描述：20 个作业、5 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=100`
  - 参考值性质：最优
  - 参考值/区间：`objective=1150`
  - 备注：未标注

- `jsplib_la15`
  - 问题描述：20 个作业、5 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=100`
  - 参考值性质：最优
  - 参考值/区间：`objective=1207`
  - 备注：未标注

- `jsplib_la16`
  - 问题描述：10 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=100`
  - 参考值性质：最优
  - 参考值/区间：`objective=945`
  - 备注：`toy`

- `jsplib_la19`
  - 问题描述：10 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=100`
  - 参考值性质：最优
  - 参考值/区间：`objective=842`
  - 备注：未标注

- `jsplib_orb01`
  - 问题描述：10 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=100`
  - 参考值性质：最优
  - 参考值/区间：`objective=1059`
  - 备注：未标注

- `jsplib_orb02`
  - 问题描述：10 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=100`
  - 参考值性质：最优
  - 参考值/区间：`objective=888`
  - 备注：未标注

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

- `jsplib_orb05`
  - 问题描述：10 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=100`
  - 参考值性质：最优
  - 参考值/区间：`objective=887`
  - 备注：未标注

- `jsplib_orb09`
  - 问题描述：10 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=100`
  - 参考值性质：最优
  - 参考值/区间：`objective=934`
  - 备注：未标注

- `jsplib_tai_10_10_10`
  - 问题描述：10 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=100`
  - 参考值性质：最优
  - 参考值/区间：`objective=8481`
  - 备注：未标注

- `jsplib_tai_10_10_3`
  - 问题描述：10 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=100`
  - 参考值性质：最优
  - 参考值/区间：`objective=8094`
  - 备注：未标注

- `jsplib_tai_10_10_6`
  - 问题描述：10 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=100`
  - 参考值性质：最优
  - 参考值/区间：`objective=8509`
  - 备注：未标注

- `jsplib_tai_10_10_8`
  - 问题描述：10 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=100`
  - 参考值性质：最优
  - 参考值/区间：`objective=7788`
  - 备注：未标注

- `jsplib_la21`
  - 问题描述：15 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=150`
  - 参考值性质：最优
  - 参考值/区间：`objective=1046`
  - 备注：`toy`

- `jsplib_la22`
  - 问题描述：15 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=150`
  - 参考值性质：最优
  - 参考值/区间：`objective=927`
  - 备注：未标注

- `jsplib_la23`
  - 问题描述：15 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=150`
  - 参考值性质：最优
  - 参考值/区间：`objective=1032`
  - 备注：未标注

- `jsplib_la25`
  - 问题描述：15 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=150`
  - 参考值性质：最优
  - 参考值/区间：`objective=977`
  - 备注：未标注

### full

- `jsplib_la30`
  - 问题描述：20 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=200`
  - 参考值性质：最优
  - 参考值/区间：`objective=1355`
  - 备注：未标注

- `jsplib_swv01`
  - 问题描述：20 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=200`
  - 参考值性质：最优
  - 参考值/区间：`objective=1407`
  - 备注：`toy`

- `jsplib_swv02`
  - 问题描述：20 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=200`
  - 参考值性质：最优
  - 参考值/区间：`objective=1475`
  - 备注：未标注

- `jsplib_la36`
  - 问题描述：15 个作业、15 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=225`
  - 参考值性质：最优
  - 参考值/区间：`objective=1268`
  - 备注：`toy`

- `jsplib_abz7`
  - 问题描述：20 个作业、15 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=300`
  - 参考值性质：最优
  - 参考值/区间：`objective=656`
  - 备注：`easy`

- `jsplib_dmu01`
  - 问题描述：20 个作业、15 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=300`
  - 参考值性质：最优
  - 参考值/区间：`objective=2563`
  - 备注：`medium`

- `jsplib_dmu41`
  - 问题描述：20 个作业、15 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=300`
  - 参考值性质：可行（最好已知上界）
  - 参考值/区间：`lower_bound=3176`，`upper_bound=3248`
  - 备注：`open`

- `jsplib_la31`
  - 问题描述：30 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=300`
  - 参考值性质：最优
  - 参考值/区间：`objective=1784`
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

- `jsplib_dmu46`
  - 问题描述：20 个作业、20 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=400`
  - 参考值性质：可行（最好已知上界）
  - 参考值/区间：`lower_bound=3780`，`upper_bound=4035`
  - 备注：`open`

- `jsplib_ta21js`
  - 问题描述：20 个作业、20 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=400`
  - 参考值性质：最优
  - 参考值/区间：`objective=1642`
  - 备注：`medium`

- `jsplib_yn1`
  - 问题描述：20 个作业、20 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=400`
  - 参考值性质：最优
  - 参考值/区间：`objective=884`
  - 备注：`hard`

- `jsplib_dmu51`
  - 问题描述：30 个作业、15 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=450`
  - 参考值性质：可行（最好已知上界）
  - 参考值/区间：`lower_bound=4070`，`upper_bound=4151`
  - 备注：`open`

- `jsplib_ta31js`
  - 问题描述：30 个作业、15 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=450`
  - 参考值性质：最优
  - 参考值/区间：`objective=1764`
  - 备注：`easy`

### pressure

- `jsplib_swv11`
  - 问题描述：50 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=500`
  - 参考值性质：最优
  - 参考值/区间：`objective=2983`
  - 备注：`medium`

- `jsplib_swv13`
  - 问题描述：50 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=500`
  - 参考值性质：最优
  - 参考值/区间：`objective=3104`
  - 备注：未标注

- `jsplib_swv16`
  - 问题描述：50 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=500`
  - 参考值性质：最优
  - 参考值/区间：`objective=2924`
  - 备注：`toy`

- `jsplib_swv18`
  - 问题描述：50 个作业、10 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=500`
  - 参考值性质：最优
  - 参考值/区间：`objective=2852`
  - 备注：未标注

- `jsplib_dmu56`
  - 问题描述：30 个作业、20 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=600`
  - 参考值性质：可行（最好已知上界）
  - 参考值/区间：`lower_bound=4755`，`upper_bound=4934`
  - 备注：`open`

- `jsplib_dmu59`
  - 问题描述：30 个作业、20 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=600`
  - 参考值性质：可行（最好已知上界）
  - 参考值/区间：`lower_bound=4366`，`upper_bound=4607`
  - 备注：未标注

- `jsplib_ta41js`
  - 问题描述：30 个作业、20 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=600`
  - 参考值性质：可行（最好已知上界）
  - 参考值/区间：`lower_bound=1926`，`upper_bound=2005`
  - 备注：`open`

- `jsplib_dmu32`
  - 问题描述：50 个作业、15 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=750`
  - 参考值性质：最优
  - 参考值/区间：`objective=5927`
  - 备注：未标注

- `jsplib_dmu73`
  - 问题描述：50 个作业、15 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=750`
  - 参考值性质：可行（最好已知上界）
  - 参考值/区间：`lower_bound=6107`，`upper_bound=6132`
  - 备注：未标注

- `jsplib_ta51js`
  - 问题描述：50 个作业、15 台机器的 job-shop 调度问题，目标是最小化 makespan。
  - 规模：`operations=750`
  - 参考值性质：最优
  - 参考值/区间：`objective=2760`
  - 备注：`toy`

共 65 个 case。
