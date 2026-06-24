# QAPLIB 数据来源说明

QAPLIB 目录保存来自 QAPLIB 的 quadratic assignment benchmark case。

## 相关 case

- `qaplib_nug12`
  - 问题描述：12 设施/12 位置的 quadratic assignment 问题。
  - 规模：`facilities=12`，`locations=12`
  - 参考值：`objective=578`
- `qaplib_nug20`
  - 问题描述：20 设施/20 位置的 quadratic assignment 问题。
  - 规模：`facilities=20`，`locations=20`
  - 参考值：`objective=2570`
- `qaplib_had20`
  - 问题描述：20 设施/20 位置的 quadratic assignment 问题。
  - 规模：`facilities=20`，`locations=20`
  - 参考值：以对应 case 定义为准。
- `qaplib_lipa40a`
  - 问题描述：40 设施/40 位置的 quadratic assignment 问题。
  - 规模：`facilities=40`，`locations=40`
  - 参考值：以对应 case 定义为准。
- `qaplib_chr12a`
  - 问题描述：12 设施/12 位置的 quadratic assignment 问题。
  - 规模：`facilities=12`，`locations=12`
  - 参考值：以对应 case 定义为准。

## 问题定义

每个 case 都是在给定流量矩阵和距离矩阵的前提下，寻找设施到位置的最优置换，使总分配成本最小。
