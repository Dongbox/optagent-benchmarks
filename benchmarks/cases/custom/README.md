# Custom 数据来源说明

`custom/` 保存 OptAgent 自定义 benchmark。这里的 case 优先表达具体问题建模和实例规模，而不是模拟外部公开数据集命名。

## 相关 case

- `steel_transition_sequence`
  - 问题定义：钢卷续接排序。在给定钢卷集合中寻找一个开放顺序，使相邻钢卷尽可能满足焊接条件，目标是最小化不可直接焊接的相邻转移次数。