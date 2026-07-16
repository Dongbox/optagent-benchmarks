# TSPLIB 数据来源说明

TSPLIB 目录保存来自 [TSPLIB95](https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/) 的路由类 benchmark case，当前注册 43 个对称旅行商问题（TSP）。case 按 `smoke`、`calibration`、`full` 和 `pressure` 分层，完整清单由 registry 提供。

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

每个 case 都是在给定城市集合中寻找一条最短哈密顿回路。模型使用 sequence variable，并根据 `model_style` 通过 `sequence_transition_sum` 或确定性的 external callback 计算闭合 tour 长度。支持 `EUC_2D`、`CEIL_2D`、`ATT`、`GEO` 和 `EXPLICIT` 距离格式；独立验证重新检查 Hamiltonian permutation 和完整回路长度。
