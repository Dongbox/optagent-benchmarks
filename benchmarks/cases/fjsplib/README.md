# FJSPLIB 数据来源说明

FJSPLIB 目录保存来自 [SchedulingLab FJSP archive](https://github.com/SchedulingLab/fjsp-instances) 的 flexible job-shop benchmark case。当前注册 66 个 case，按 `smoke`、`calibration`、`full` 和 `pressure` 四个 tier 管理，具体 case ID、规模和 reference 以 registry 为准。

## 数据格式

- 原始 `.txt` 和标准化 `.json` 证据位于 `fjobshop/raw/`；
- 离线运行以标准化 JSON 为 loader 契约；
- JSON 记录 jobs、machines、operations、候选机器、加工时间和 reference 来源；
- `reference.kind=optimum` 表示已闭合最优值，`bounds` 表示受治理的上下界或 best-known。

当前 tier 分布为：`smoke=12`、`calibration=24`、`full=24`、`pressure=6`。完整清单通过 registry 查询；以下按 tier 列出当前 case。

## 相关 case

### smoke

- `fjsplib_sfjs02`
  - 规模：`jobs=2`，`machines=2`，`operations=4`，`candidates=6`
  - 参考值：`objective=107`，reference kind 为 `optimum`。
- `fjsplib_sfjs01`
  - 规模：`jobs=2`，`machines=2`，`operations=4`，`candidates=8`
  - 参考值：`objective=66`，reference kind 为 `optimum`。
- `fjsplib_sfjs04`
  - 规模：`jobs=3`，`machines=2`，`operations=6`，`candidates=10`
  - 参考值：`objective=355`，reference kind 为 `optimum`。
- `fjsplib_sfjs05`
  - 规模：`jobs=3`，`machines=2`，`operations=6`，`candidates=12`
  - 参考值：`lower_bound=107`，`upper_bound=119`，reference kind 为 `bounds`。
- `fjsplib_sfjs06`
  - 规模：`jobs=3`，`machines=3`，`operations=9`，`candidates=15`
  - 参考值：`lower_bound=310`，`upper_bound=320`，reference kind 为 `bounds`。
- `fjsplib_sfjs07`
  - 规模：`jobs=3`，`machines=5`，`operations=9`，`candidates=18`
  - 参考值：`objective=397`，reference kind 为 `optimum`。
- `fjsplib_sfjs09`
  - 规模：`jobs=3`，`machines=3`，`operations=9`，`candidates=18`
  - 参考值：`objective=210`，reference kind 为 `optimum`。
- `fjsplib_sfjs10`
  - 规模：`jobs=4`，`machines=5`，`operations=12`，`candidates=20`
  - 参考值：`lower_bound=427`，`upper_bound=516`，reference kind 为 `bounds`。
- `fjsplib_mfjs02`
  - 规模：`jobs=5`，`machines=7`，`operations=15`，`candidates=39`
  - 参考值：`lower_bound=396`，`upper_bound=446`，reference kind 为 `bounds`。
- `fjsplib_k1`
  - 规模：`jobs=4`，`machines=5`，`operations=12`，`candidates=60`
  - 参考值：`objective=11`，reference kind 为 `optimum`。
- `fjsplib_k2`
  - 规模：`jobs=10`，`machines=7`，`operations=29`，`candidates=203`
  - 参考值：`objective=11`，reference kind 为 `optimum`。
- `fjsplib_k3`
  - 规模：`jobs=10`，`machines=10`，`operations=30`，`candidates=300`
  - 参考值：`objective=7`，reference kind 为 `optimum`。

### calibration

- `fjsplib_mt10c1`
  - 规模：`jobs=10`，`machines=11`，`operations=100`，`candidates=110`
  - 参考值：`objective=927`，reference kind 为 `optimum`。
- `fjsplib_mt10xxx`
  - 规模：`jobs=10`，`machines=13`，`operations=100`，`candidates=130`
  - 参考值：`objective=918`，reference kind 为 `optimum`。
- `fjsplib_sm01_1`
  - 规模：`jobs=10`，`machines=20`，`operations=50`，`candidates=304`
  - 参考值：`lower_bound=70`，`upper_bound=91`，reference kind 为 `bounds`。
- `fjsplib_med01_4`
  - 规模：`jobs=10`，`machines=40`，`operations=50`，`candidates=564`
  - 参考值：`lower_bound=70`，`upper_bound=87`，reference kind 为 `bounds`。
- `fjsplib_sm02_5`
  - 规模：`jobs=20`，`machines=20`，`operations=100`，`candidates=612`
  - 参考值：`lower_bound=81`，`upper_bound=133`，reference kind 为 `bounds`。
- `fjsplib_mk01`
  - 规模：`jobs=10`，`machines=6`，`operations=55`，`candidates=115`
  - 参考值：`objective=40`，reference kind 为 `optimum`。
- `fjsplib_mk02`
  - 规模：`jobs=10`，`machines=6`，`operations=58`，`candidates=238`
  - 参考值：`lower_bound=24`，`upper_bound=26`，reference kind 为 `bounds`。
- `fjsplib_mk04`
  - 规模：`jobs=15`，`machines=8`，`operations=90`，`candidates=172`
  - 参考值：`objective=60`，reference kind 为 `optimum`。
- `fjsplib_mk07`
  - 规模：`jobs=20`，`machines=5`，`operations=100`，`candidates=283`
  - 参考值：`lower_bound=133`，`upper_bound=139`，reference kind 为 `bounds`。
- `fjsplib_mfjs07`
  - 规模：`jobs=8`，`machines=7`，`operations=32`，`candidates=78`
  - 参考值：`lower_bound=764`，`upper_bound=879`，reference kind 为 `bounds`。
- `fjsplib_e-mt06`
  - 规模：`jobs=6`，`machines=6`，`operations=36`，`candidates=42`
  - 参考值：`objective=55`，reference kind 为 `optimum`。
- `fjsplib_v-mt06`
  - 规模：`jobs=6`，`machines=6`，`operations=36`，`candidates=103`
  - 参考值：`objective=47`，reference kind 为 `optimum`。
- `fjsplib_e-car7`
  - 规模：`jobs=7`，`machines=7`，`operations=49`，`candidates=58`
  - 参考值：`lower_bound=4216`，`upper_bound=6123`，reference kind 为 `bounds`。
- `fjsplib_e-la03`
  - 规模：`jobs=10`，`machines=5`，`operations=50`，`candidates=59`
  - 参考值：`objective=550`，reference kind 为 `optimum`。
- `fjsplib_v-la05`
  - 规模：`jobs=10`，`machines=5`，`operations=50`，`candidates=119`
  - 参考值：`objective=457`，reference kind 为 `optimum`。
- `fjsplib_e-car2`
  - 规模：`jobs=13`，`machines=4`，`operations=52`，`candidates=63`
  - 参考值：`lower_bound=5929`，`upper_bound=6455`，reference kind 为 `bounds`。
- `fjsplib_v-car8`
  - 规模：`jobs=8`，`machines=8`，`operations=64`，`candidates=254`
  - 参考值：`objective=4613`，reference kind 为 `optimum`。
- `fjsplib_r-car6`
  - 规模：`jobs=8`，`machines=9`，`operations=72`，`candidates=140`
  - 参考值：`lower_bound=5486`，`upper_bound=6147`，reference kind 为 `bounds`。
- `fjsplib_e-abz5`
  - 规模：`jobs=10`，`machines=10`，`operations=100`，`candidates=113`
  - 参考值：`lower_bound=859`，`upper_bound=1176`，reference kind 为 `bounds`。
- `fjsplib_e-la11`
  - 规模：`jobs=20`，`machines=5`，`operations=100`，`candidates=113`
  - 参考值：`objective=1103`，reference kind 为 `optimum`。
- `fjsplib_r-la17`
  - 规模：`jobs=10`，`machines=10`，`operations=100`，`candidates=193`
  - 参考值：`objective=646`，reference kind 为 `optimum`。
- `fjsplib_v-orb7`
  - 规模：`jobs=10`，`machines=10`，`operations=100`，`candidates=456`
  - 参考值：`objective=275`，reference kind 为 `optimum`。
- `fjsplib_v-abz5`
  - 规模：`jobs=10`，`machines=10`，`operations=100`，`candidates=467`
  - 参考值：`lower_bound=859`，`upper_bound=860`，reference kind 为 `bounds`。
- `fjsplib_k4`
  - 规模：`jobs=15`，`machines=10`，`operations=56`，`candidates=560`
  - 参考值：`objective=12`，reference kind 为 `optimum`。

### full

- `fjsplib_setb4c9`
  - 规模：`jobs=15`，`machines=11`，`operations=150`，`candidates=165`
  - 参考值：`objective=914`，reference kind 为 `optimum`。
- `fjsplib_seti5xxx`
  - 规模：`jobs=15`，`machines=18`，`operations=225`，`candidates=270`
  - 参考值：`objective=1194`，reference kind 为 `optimum`。
- `fjsplib_lar01_3`
  - 规模：`jobs=10`，`machines=60`，`operations=50`，`candidates=964`
  - 参考值：`lower_bound=68`，`upper_bound=86`，reference kind 为 `bounds`。
- `fjsplib_med02_2`
  - 规模：`jobs=20`，`machines=40`，`operations=100`，`candidates=1192`
  - 参考值：`lower_bound=81`，`upper_bound=132`，reference kind 为 `bounds`。
- `fjsplib_sm03_4`
  - 规模：`jobs=50`，`machines=20`，`operations=250`，`candidates=1524`
  - 参考值：`lower_bound=164`，`upper_bound=258`，reference kind 为 `bounds`。
- `fjsplib_mk05`
  - 规模：`jobs=15`，`machines=4`，`operations=106`，`candidates=181`
  - 参考值：`lower_bound=168`，`upper_bound=172`，reference kind 为 `bounds`。
- `fjsplib_mk03`
  - 规模：`jobs=15`，`machines=8`，`operations=150`，`candidates=451`
  - 参考值：`objective=204`，reference kind 为 `optimum`。
- `fjsplib_mk06`
  - 规模：`jobs=10`，`machines=10`，`operations=150`，`candidates=490`
  - 参考值：`lower_bound=33`，`upper_bound=58`，reference kind 为 `bounds`。
- `fjsplib_mk11`
  - 规模：`jobs=30`，`machines=5`，`operations=179`，`candidates=270`
  - 参考值：`lower_bound=594`，`upper_bound=615`，reference kind 为 `bounds`。
- `fjsplib_mk12`
  - 规模：`jobs=30`，`machines=10`，`operations=193`，`candidates=288`
  - 参考值：`objective=508`，reference kind 为 `optimum`。
- `fjsplib_mk08`
  - 规模：`jobs=20`，`machines=10`，`operations=225`，`candidates=322`
  - 参考值：`objective=523`，reference kind 为 `optimum`。
- `fjsplib_mk13`
  - 规模：`jobs=30`，`machines=10`，`operations=231`，`candidates=778`
  - 参考值：`lower_bound=353`，`upper_bound=430`，reference kind 为 `bounds`。
- `fjsplib_mk09`
  - 规模：`jobs=20`，`machines=10`，`operations=240`，`candidates=606`
  - 参考值：`objective=307`，reference kind 为 `optimum`。
- `fjsplib_mk10`
  - 规模：`jobs=20`，`machines=15`，`operations=240`，`candidates=716`
  - 参考值：`lower_bound=175`，`upper_bound=197`，reference kind 为 `bounds`。
- `fjsplib_mk14`
  - 规模：`jobs=30`，`machines=15`，`operations=277`，`candidates=432`
  - 参考值：`objective=694`，reference kind 为 `optimum`。
- `fjsplib_dpp01`
  - 规模：`jobs=10`，`machines=5`，`operations=196`，`candidates=221`
  - 参考值：`lower_bound=2505`，`upper_bound=2518`，reference kind 为 `bounds`。
- `fjsplib_dpp04`
  - 规模：`jobs=10`，`machines=5`，`operations=196`，`candidates=221`
  - 参考值：`objective=2503`，reference kind 为 `optimum`。
- `fjsplib_dpp05`
  - 规模：`jobs=10`，`machines=5`，`operations=196`，`candidates=332`
  - 参考值：`lower_bound=2189`，`upper_bound=2216`，reference kind 为 `bounds`。
- `fjsplib_dpp09`
  - 规模：`jobs=15`，`machines=8`，`operations=293`，`candidates=1182`
  - 参考值：`lower_bound=2061`，`upper_bound=2066`，reference kind 为 `bounds`。
- `fjsplib_v-la27`
  - 规模：`jobs=20`，`machines=10`，`operations=200`，`candidates=915`
  - 参考值：`objective=1084`，reference kind 为 `optimum`。
- `fjsplib_r-la39`
  - 规模：`jobs=15`，`machines=15`，`operations=225`，`candidates=436`
  - 参考值：`objective=1011`，reference kind 为 `optimum`。
- `fjsplib_e-abz7`
  - 规模：`jobs=20`，`machines=15`，`operations=300`，`candidates=339`
  - 参考值：`lower_bound=492`，`upper_bound=638`，reference kind 为 `bounds`。
- `fjsplib_e-la33`
  - 规模：`jobs=30`，`machines=10`，`operations=300`，`candidates=339`
  - 参考值：`objective=1547`，reference kind 为 `optimum`。
- `fjsplib_v-abz7`
  - 规模：`jobs=20`，`machines=15`，`operations=300`，`candidates=1951`
  - 参考值：`lower_bound=492`，`upper_bound=495`，reference kind 为 `bounds`。

### pressure

- `fjsplib_med03_2`
  - 规模：`jobs=50`，`machines=40`，`operations=250`，`candidates=3052`
  - 参考值：`lower_bound=77`，`upper_bound=259`，reference kind 为 `bounds`。
- `fjsplib_sm04_3`
  - 规模：`jobs=100`，`machines=20`，`operations=500`，`candidates=3164`
  - 参考值：`lower_bound=321`，`upper_bound=555`，reference kind 为 `bounds`。
- `fjsplib_dpp13`
  - 规模：`jobs=20`，`machines=10`，`operations=387`，`candidates=518`
  - 参考值：`lower_bound=2161`，`upper_bound=2257`，reference kind 为 `bounds`。
- `fjsplib_dpp16`
  - 规模：`jobs=20`，`machines=10`，`operations=387`，`candidates=518`
  - 参考值：`lower_bound=2148`，`upper_bound=2255`，reference kind 为 `bounds`。
- `fjsplib_dpp17`
  - 规模：`jobs=20`，`machines=10`，`operations=387`，`candidates=1156`
  - 参考值：`lower_bound=2088`，`upper_bound=2140`，reference kind 为 `bounds`。
- `fjsplib_dpp15`
  - 规模：`jobs=20`，`machines=10`，`operations=387`，`candidates=1941`
  - 参考值：`lower_bound=2161`，`upper_bound=2165`，reference kind 为 `bounds`。

## 问题定义

每个 case 都是在满足每道工序的机器选择、作业内工序先后和机器不重叠约束的前提下，最小化项目 makespan。

## 模型与验证

每个 operation 为候选机器创建 optional interval，使用 presence 和 `exactly_one` 选择机器。选中 interval 的 start/end projection 定义工序前置关系；每台机器使用 sequence/no-overlap 约束避免重叠，目标最小化 makespan。当前 model style 为 `optional_interval_machine_choice_no_overlap_precedence`。

独立验证检查每个 operation 恰好选择一个机器、工序前置、机器 sequence 是合法 permutation、机器不重叠，并重新计算 makespan；不信任求解器报告的 feasibility 或 objective。

```bash
./.venv/bin/python benchmark.py list-cases --family flexible_interval_job_shop
```
