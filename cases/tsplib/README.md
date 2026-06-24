# TSPLIB 数据来源说明

TSPLIB 目录保存来自 TSPLIB95 的路由类 benchmark case，当前是对称旅行商问题（TSP）。

## 相关 case

- `tsplib_pr76`
  - 问题描述：76 城市对称 TSP，目标是最小化哈密顿回路长度。
  - 规模：`nodes=76`
  - 参考值：`objective=108159`
- `tsplib_kroa100`
  - 问题描述：100 城市对称 TSP。
  - 规模：`nodes=100`
  - 参考值：`objective=21282`
- `tsplib_a280`
  - 问题描述：280 城市对称 TSP。
  - 规模：`nodes=280`
  - 参考值：`objective=2579`
- `tsplib_berlin52`
  - 问题描述：52 城市对称 TSP。
  - 规模：`nodes=52`
  - 参考值：`objective=7542`
- `tsplib_eil51`
  - 问题描述：51 城市对称 TSP。
  - 规模：`nodes=51`
  - 参考值：`objective=426`

## 问题定义

每个 case 都是在给定城市集合中寻找一条最短哈密顿回路。模型会根据不同 `model_style` 使用 sequence 变量和距离矩阵或外部回调来计算路径长度。
