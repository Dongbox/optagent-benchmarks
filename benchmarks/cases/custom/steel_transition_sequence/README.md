# Steel Transition Sequence 数据来源说明

## 数据来源说明

Steel Transition Sequence 是 OptAgent 自定义的钢卷续接排序数据集，用于评估基于序列转移图的开放路径优化模型。

数据集来源：

- 自定义钢卷属性数据：`benchmarks/cases/custom/steel_transition_sequence/data/steel_coils.json`
- 303 节点样例：`sample.xlsx`；其参考排列位于 `answer.xlsx`
- 900/1000 节点预计算兼容图：`graphs_dense_900.jsonl.gz`、`graphs_sparse_1000.jsonl.gz`
- 图实例的 CP-SAT 精确结果：`cp_sat_optimal_results_900.csv`、`cp_sat_optimal_results_1000.csv`

## 问题说明

给定全部钢卷，寻找一条恰好经过每个钢卷一次的开放排列路径。相邻钢卷可直接焊接时转移成本为 0，否则成本为 1；目标是最小化总转移成本，即不可直接续接的相邻对数量。

## 数据筛选依据

- 数据规模定义：`coils`，即排列中的钢卷/图节点数量。

tier 分类范围：

| tier | case 数量 | coils 范围 |
|---|---:|---:|
| smoke | 1 | 5 |
| calibration | 1 | 40 |
| full | 2 | 285–303 |
| pressure | 20 | 900–1000 |

- 筛选策略：toy、bundled 与 bundled_head40 用于基本功能及中小规模验证；303 节点 sample 用于完整属性数据验证；900、1000 节点组保留各 10 个预计算兼容图实例，用于稀疏兼容图下的压力测试。图实例的参考值由 CP-SAT 精确结果提供。

## 建模说明

使用 `sequence_var` 表示钢卷的全排列，使用 `sequence_transition_sum` 对完整 0/1 转移矩阵求和，且 `include_return_edge=False`，因此模型是开放路径而非闭环。所有节点对均有有限成本，故任意排列均可行；可焊接边为 0，不可焊接边为 1。

- 适用的求解方式：`solve()` 的 GA 策略适用。模型将完整转移图以原生接口提供给 OptAgent，不使用 `external_call` 黑盒目标。

## 特殊备注

sample 与 bundled 数据由九维钢卷属性计算兼容关系；900/1000 数据直接读取预计算兼容图并转换为相同的完整 0/1 成本矩阵。目标不计末尾钢卷返回首钢卷的成本。

## 相关 case

### smoke

- `custom_steel_sequence_toy`
  - 问题描述：钢卷续接排序，最小化开放路径相邻转移成本。
  - 规模：`coils=5`
  - 参考值：最优
  - 参考值/区间：`objective=3`
  - 备注：穷举排列可验证。

### calibration

- `custom_steel_sequence_bundled_head40`
  - 问题描述：钢卷续接排序，最小化开放路径相邻转移成本。
  - 规模：`coils=40`
  - 参考值：最优
  - 参考值/区间：`objective=3`
  - 备注：CP-SAT 已证明最优。

### full

- `custom_steel_sequence_bundled`
  - 问题描述：钢卷续接排序，最小化开放路径相邻转移成本。
  - 规模：`coils=285`
  - 参考值：最优
  - 参考值/区间：`objective=1`
  - 备注：CP-SAT 已证明最优。
- `custom_steel_sequence_sample303`
  - 问题描述：钢卷续接排序，最小化开放路径相邻转移成本。
  - 规模：`coils=303`
  - 参考值：最优
  - 参考值/区间：`objective=1`
  - 备注：CP-SAT 已证明最优。

### pressure

- `custom_steel_sequence_graph900_00` 至 `custom_steel_sequence_graph900_09`
  - 问题描述：预计算兼容图上的钢卷续接排序，最小化开放路径相邻转移成本。
  - 规模：每例 `coils=900`
  - 参考值：最优
  - 参考值/区间：每例 `objective=0`
  - 备注：CP-SAT 已证明最优。
- `custom_steel_sequence_graph1000_00` 至 `custom_steel_sequence_graph1000_09`
  - 问题描述：预计算兼容图上的钢卷续接排序，最小化开放路径相邻转移成本。
  - 规模：每例 `coils=1000`
  - 参考值：最优
  - 参考值/区间：`graph1000_00`、`graph1000_07` 为 `objective=1`，其余为 `objective=0`
  - 备注：CP-SAT 已证明最优。

共 24 个 case。