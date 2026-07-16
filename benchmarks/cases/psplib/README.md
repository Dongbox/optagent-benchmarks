# PSPLIB 数据来源说明

PSPLIB 目录保存来自 ScheduleOpt 归档的 PSPLIB j90 系列 benchmark case，当前是资源受限项目调度问题（RCPSP）。

## 相关 case

- `psplib_j90_1_1`
  - 问题描述：90 个活动、4 个可再生资源的 RCPSP。
  - 规模：`activities=90`，`renewable_resources=4`
  - 参考值：`objective=73`
- `psplib_j90_1_8`
  - 问题描述：90 个活动、4 个可再生资源的 RCPSP。
  - 规模：`activities=90`，`renewable_resources=4`
  - 参考值：`objective=95`
- `psplib_j90_2_4`
  - 问题描述：90 个活动、4 个可再生资源的 RCPSP。
  - 规模：`activities=90`，`renewable_resources=4`
  - 参考值：`objective=70`
- `psplib_j90_5_3`
  - 问题描述：90 个活动、4 个可再生资源的 RCPSP。
  - 规模：`activities=90`，`renewable_resources=4`
  - 参考值：`objective=87`
- `psplib_j90_6_7`
  - 问题描述：90 个活动、4 个可再生资源的 RCPSP。
  - 规模：`activities=90`，`renewable_resources=4`
  - 参考值：`objective=71`

## 问题定义

每个 case 都是在满足活动优先关系和资源容量约束的前提下，最小化项目 makespan。
