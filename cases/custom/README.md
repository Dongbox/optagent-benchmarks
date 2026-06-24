# Custom 数据来源说明

`custom/` 保存 OptAgent 自定义 benchmark。这里的 case 优先表达具体问题建模和实例规模，而不是模拟外部公开数据集命名。

## 相关 case

- `custom_steel_sequence_toy`
  - 问题描述：5 个钢卷的转序问题，目标是最小化相邻不可焊接转移次数。
  - 规模：`coils=5`
  - 参考值：`objective=3`
- `custom_steel_sequence_bundled_head40`
  - 问题描述：从 bundled 数据前 40 个钢卷得到的转序问题。
  - 规模：`coils=40`
  - 参考值：`objective=22`
- `custom_steel_sequence_bundled`
  - 问题描述：完整 bundled 钢卷数据的转序问题。
  - 规模：`coils=285`
  - 参考值：`objective=1`

## 问题定义

当前自定义示例是钢卷转序问题：在给定钢卷集合中寻找一个顺序，使相邻钢卷尽可能满足焊接条件；不可直接焊接的相邻转移会产生罚分。

## 相关文件

- [cases/custom/steel_transition_sequence/_domain.py](steel_transition_sequence/_domain.py)
- [cases/custom/steel_transition_sequence/toy.py](steel_transition_sequence/toy.py)
- [cases/custom/steel_transition_sequence/bundled.py](steel_transition_sequence/bundled.py)
- [cases/custom/steel_transition_sequence/data/steel_coils.json](steel_transition_sequence/data/steel_coils.json)
