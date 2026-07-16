# MIPLIB 2017 数据来源说明

MIPLIB 2017 目录保存来自 MIPLIB 2017 benchmark-v2 的线性混合整数规划 case。

## 相关 case

- `miplib2017_reblock115`
  - 问题描述：1150 个二进制变量、4735 条约束的线性 MIP。
  - 规模：`variables=1150`，`constraints=4735`
  - 参考值：`objective=-36800603.2332`
- `miplib2017_air05`
  - 问题描述：以 case 定义为准的线性 MIP。
- `miplib2017_fast0507`
  - 问题描述：以 case 定义为准的线性 MIP。
- `miplib2017_50v-10`
  - 问题描述：以 case 定义为准的线性 MIP。
- `miplib2017_academictimetablesmall`
  - 问题描述：以 case 定义为准的线性 MIP。
- `miplib2017_ran14x18-disj-8`
  - 问题描述：以 case 定义为准的线性 MIP。

## 问题定义

每个 case 都是在给定 MPS 形式线性约束和整数变量的前提下，求解最优目标值。该来源主要用于 exact/MIP backend 基准，而不是主力启发式搜索家族。
