# PSPLIB

## 数据来源说明

PSPLIB 是公开的项目调度问题库；当前使用其单模式资源受限项目调度（RCPSP）j30、j60、j90 与 j120 集合。

数据集来源：

- PSPLIB 主页：https://www.om-db.wi.tum.de/psplib/
- 单模式 RCPSP 数据与参考界：https://www.om-db.wi.tum.de/psplib/getdata.php?mode=sm
- 本地完整实例数据：benchmarks/cases/psplib/rcpsp/raw/instances/
- 本地正式缓存数据：benchmarks/cases/psplib/rcpsp/raw/

## 问题说明

单模式 RCPSP 要求在满足活动优先关系及可再生资源容量约束的前提下，最小化汇活动结束时间，即项目 makespan。

## 数据筛选依据

- 数规模定义：规模仅以真实活动数 activities 定义；PSPLIB 原始文件额外包含 source 与 sink 两个 dummy 活动。

tier 分类范围：

| tier | case 数量 | activities 范围 |
|---|---:|---:|
| smoke | 20 | 30 |
| calibration | 20 | 60 |
| full | 15 | 90 |
| pressure | 10 | 120 |

- 筛选策略：特征向量包括 `activities`、每活动优先弧数、优先弧密度、关键路径下界/总工期、平均工期、工期变异系数、资源需求密度、平均/最大资源利用率代理值、资源利用率标准差、平均出度与出度标准差。对完整 2,040 个候选实例的各特征做 z-score 标准化；两个算例的近似程度定义为标准化特征向量的欧氏距离。算例到选中集合的距离取最近邻距离。每个 tier 从现有选中集出发，按最远点扩充；当最大距离与第二大距离之差至少为最大距离的 10% 时允许断层扩充，但总数分别不超过 30、30、25、20。随机起点与 70% 替换规则使用种子 `20260717`。

## 建模说明

使用固定长度 `interval_var` 表示每项活动；用 `precedence` 表示前后继关系；每类可再生资源使用 `cumulative` 约束；目标为最小化汇活动的 `interval_end`。

- 适用的求解方式：solve() 适用；solve_cpsat() 和 solve_milp() 当前不适用，因为当前模型没有提供对应的 CPSAT/MILP lowering。

## 特殊备注

非 closed case 的 `objective` 为 PSPLIB 公布的 best known upper bound（UB）。当官方 LB 文件未公布下界时，注册值为 `lower_bound=None`，下文标注“LB 未公布”。

## 相关 case

### smoke

- `psplib_j30_11_9`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=30`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=67`，`lower_bound=67`
  - 备注：无
- `psplib_j30_13_8`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=30`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=106`，`lower_bound=106`
  - 备注：无
- `psplib_j30_15_5`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=30`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=58`，`lower_bound=58`
  - 备注：无
- `psplib_j30_19_3`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=30`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=83`，`lower_bound=83`
  - 备注：无
- `psplib_j30_1_4`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=30`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=62`，`lower_bound=62`
  - 备注：无
- `psplib_j30_1_5`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=30`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=39`，`lower_bound=39`
  - 备注：无
- `psplib_j30_1_6`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=30`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=48`，`lower_bound=48`
  - 备注：无
- `psplib_j30_21_9`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=30`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=69`，`lower_bound=69`
  - 备注：无
- `psplib_j30_27_1`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=30`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=43`，`lower_bound=43`
  - 备注：无
- `psplib_j30_34_3`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=30`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=69`，`lower_bound=69`
  - 备注：无
- `psplib_j30_37_3`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=30`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=81`，`lower_bound=81`
  - 备注：无
- `psplib_j30_40_10`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=30`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=51`，`lower_bound=51`
  - 备注：无
- `psplib_j30_41_5`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=30`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=99`，`lower_bound=99`
  - 备注：无
- `psplib_j30_45_7`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=30`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=101`，`lower_bound=101`
  - 备注：无
- `psplib_j30_45_8`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=30`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=94`，`lower_bound=94`
  - 备注：无
- `psplib_j30_4_6`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=30`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=45`，`lower_bound=45`
  - 备注：无
- `psplib_j30_7_1`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=30`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=55`，`lower_bound=55`
  - 备注：无
- `psplib_j30_8_10`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=30`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=67`，`lower_bound=67`
  - 备注：无
- `psplib_j30_9_1`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=30`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=83`，`lower_bound=83`
  - 备注：无
- `psplib_j30_9_9`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=30`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=63`，`lower_bound=63`
  - 备注：无

### calibration

- `psplib_j60_13_1`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=60`，`renewable_resources=4`
  - 参考值：best known upper bound
  - 参考值/区间：`upper_bound=112`，`lower_bound=104`
  - 备注：无
- `psplib_j60_16_1`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=60`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=64`，`lower_bound=64`
  - 备注：无
- `psplib_j60_16_3`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=60`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=53`，`lower_bound=53`
  - 备注：无
- `psplib_j60_21_2`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=60`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=108`，`lower_bound=108`
  - 备注：无
- `psplib_j60_23_7`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=60`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=60`，`lower_bound=60`
  - 备注：无
- `psplib_j60_25_2`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=60`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=98`，`lower_bound=98`
  - 备注：无
- `psplib_j60_27_2`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=60`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=74`，`lower_bound=74`
  - 备注：无
- `psplib_j60_29_6`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=60`，`renewable_resources=4`
  - 参考值：best known upper bound
  - 参考值/区间：`upper_bound=154`，`lower_bound=145`
  - 备注：无
- `psplib_j60_2_3`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=60`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=78`，`lower_bound=78`
  - 备注：无
- `psplib_j60_33_5`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=60`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=108`，`lower_bound=108`
  - 备注：无
- `psplib_j60_33_8`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=60`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=79`，`lower_bound=79`
  - 备注：无
- `psplib_j60_34_4`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=60`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=83`，`lower_bound=83`
  - 备注：无
- `psplib_j60_3_3`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=60`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=105`，`lower_bound=105`
  - 备注：无
- `psplib_j60_41_6`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=60`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=134`，`lower_bound=134`
  - 备注：无
- `psplib_j60_45_2`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=60`，`renewable_resources=4`
  - 参考值：best known upper bound
  - 参考值/区间：`upper_bound=144`，`lower_bound=LB 未公布`
  - 备注：无
- `psplib_j60_45_4`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=60`，`renewable_resources=4`
  - 参考值：best known upper bound
  - 参考值/区间：`upper_bound=108`，`lower_bound=LB 未公布`
  - 备注：无
- `psplib_j60_48_1`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=60`，`renewable_resources=4`
  - 参考值：best known upper bound
  - 参考值/区间：`upper_bound=71`，`lower_bound=LB 未公布`
  - 备注：无
- `psplib_j60_48_3`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=60`，`renewable_resources=4`
  - 参考值：best known upper bound
  - 参考值/区间：`upper_bound=84`，`lower_bound=LB 未公布`
  - 备注：无
- `psplib_j60_5_1`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=60`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=76`，`lower_bound=76`
  - 备注：无
- `psplib_j60_9_6`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=60`，`renewable_resources=4`
  - 参考值：best known upper bound
  - 参考值/区间：`upper_bound=111`，`lower_bound=105`
  - 备注：无

### full

- `psplib_j90_13_2`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=90`，`renewable_resources=4`
  - 参考值：best known upper bound
  - 参考值/区间：`upper_bound=127`，`lower_bound=118`
  - 备注：无
- `psplib_j90_16_7`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=90`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=65`，`lower_bound=65`
  - 备注：无
- `psplib_j90_17_10`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=90`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=89`，`lower_bound=89`
  - 备注：无
- `psplib_j90_19_5`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=90`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=66`，`lower_bound=66`
  - 备注：无
- `psplib_j90_1_8`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=90`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=95`，`lower_bound=95`
  - 备注：无
- `psplib_j90_29_1`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=90`，`renewable_resources=4`
  - 参考值：best known upper bound
  - 参考值/区间：`upper_bound=135`，`lower_bound=125`
  - 备注：无
- `psplib_j90_32_9`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=90`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=95`，`lower_bound=95`
  - 备注：无
- `psplib_j90_33_1`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=90`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=99`，`lower_bound=99`
  - 备注：无
- `psplib_j90_35_6`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=90`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=72`，`lower_bound=72`
  - 备注：无
- `psplib_j90_36_9`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=90`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=102`，`lower_bound=102`
  - 备注：无
- `psplib_j90_41_9`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=90`，`renewable_resources=4`
  - 参考值：best known upper bound
  - 参考值/区间：`upper_bound=118`，`lower_bound=109`
  - 备注：无
- `psplib_j90_45_5`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=90`，`renewable_resources=4`
  - 参考值：best known upper bound
  - 参考值/区间：`upper_bound=173`，`lower_bound=164`
  - 备注：无
- `psplib_j90_47_10`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=90`，`renewable_resources=4`
  - 参考值：best known upper bound
  - 参考值/区间：`upper_bound=65`，`lower_bound=LB 未公布`
  - 备注：无
- `psplib_j90_47_5`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=90`，`renewable_resources=4`
  - 参考值：best known upper bound
  - 参考值/区间：`upper_bound=93`，`lower_bound=LB 未公布`
  - 备注：无
- `psplib_j90_6_7`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=90`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=71`，`lower_bound=71`
  - 备注：无

### pressure

- `psplib_j120_16_3`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=120`，`renewable_resources=4`
  - 参考值：best known upper bound
  - 参考值/区间：`upper_bound=233`，`lower_bound=219`
  - 备注：无
- `psplib_j120_1_3`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=120`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=125`，`lower_bound=125`
  - 备注：无
- `psplib_j120_20_9`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=120`，`renewable_resources=4`
  - 参考值：best known upper bound
  - 参考值/区间：`upper_bound=80`，`lower_bound=LB 未公布`
  - 备注：无
- `psplib_j120_27_5`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=120`，`renewable_resources=4`
  - 参考值：best known upper bound
  - 参考值/区间：`upper_bound=111`，`lower_bound=LB 未公布`
  - 备注：无
- `psplib_j120_44_10`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=120`，`renewable_resources=4`
  - 参考值：best known upper bound
  - 参考值/区间：`upper_bound=98`，`lower_bound=LB 未公布`
  - 备注：无
- `psplib_j120_49_5`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=120`，`renewable_resources=4`
  - 参考值：best known upper bound
  - 参考值/区间：`upper_bound=89`，`lower_bound=LB 未公布`
  - 备注：无
- `psplib_j120_56_4`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=120`，`renewable_resources=4`
  - 参考值：best known upper bound
  - 参考值/区间：`upper_bound=221`，`lower_bound=LB 未公布`
  - 备注：无
- `psplib_j120_56_9`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=120`，`renewable_resources=4`
  - 参考值：best known upper bound
  - 参考值/区间：`upper_bound=287`，`lower_bound=LB 未公布`
  - 备注：无
- `psplib_j120_58_8`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=120`，`renewable_resources=4`
  - 参考值：best known upper bound
  - 参考值/区间：`upper_bound=132`，`lower_bound=LB 未公布`
  - 备注：无
- `psplib_j120_5_3`
  - 问题描述：单模式 RCPSP，最小化项目 makespan。
  - 规模：`activities=120`，`renewable_resources=4`
  - 参考值：最优
  - 参考值/区间：`upper_bound=72`，`lower_bound=72`
  - 备注：无

共 65 个 case。
