# 自定义 Cases

`custom/` 保存 benchmark 自有、并非公共数据集镜像的业务实例。

当前钢卷转序 family 对钢卷排序，并最小化相邻钢卷无法直接焊接产生的惩罚。它覆盖
sequence variable 和 external transition cost 建模，包含 toy、缩减数据和 bundled data
三个规模层级。

关键文件：

- `steel_transition_sequence/_domain.py`
- `steel_transition_sequence/toy.py`
- `steel_transition_sequence/bundled.py`
- `steel_transition_sequence/data/steel_coils.json`

当前 ID、tier、规模和 reference 通过以下命令查询：

```bash
./.venv/bin/python benchmark.py list-cases --family sequence_transition_penalty
```

自定义 reference 与公共 case 一样，必须记录来源并通过独立解验证。
