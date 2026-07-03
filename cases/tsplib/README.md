# TSPLIB 数据来源说明

TSPLIB 目录保存来自 TSPLIB95 的 routing benchmark case。当前正式注册的是对称旅行商问题（TSP），用于测试 OptAgent 在 permutation / sequence 路由优化问题上的表现。

数据集来源：

- TSPLIB95 主页：https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/
- TSP 实例归档：https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/
- 镜像数据：https://github.com/mastqe/tsplib

参考解来源：

- TSPLIB95 symmetric TSP 页面：https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/STSP.html
- 本地整理表：`benchmarks/cases/tsplib/tsp/raw/ALL_tsp/stsp_optimal_solutions.csv`

本地完整数据集缓存保存在：

```text
benchmarks/cases/tsplib/tsp/raw/ALL_tsp/
```

筛选后正式注册 case 的 `.tsp` 文件会复制到 `tsp/raw/` 根层，保证 `--no-download` 时可直接运行。

## 距离类型说明

当前 TSP loader 支持 TSPLIB 中本轮注册 case 用到的距离类型：

- `EUC_2D`：二维欧氏距离，按 TSPLIB 规则四舍五入。
- `CEIL_2D`：二维欧氏距离，向上取整。
- `ATT`：pseudo-Euclidean 距离。
- `GEO`：地理坐标距离。
- `EXPLICIT`：显式距离矩阵，支持 `FULL_MATRIX`、`UPPER_ROW`、`LOWER_ROW`、`UPPER_DIAG_ROW`、`LOWER_DIAG_ROW`。

## 相关 case

<!-- tsplib-stat-formulas:start -->

### 统计特征说明

下面两个统计量都使用当前 `tsp/raw/` 中缓存的 `.tsp` 文件，并按 benchmark loader 实际采用的 TSPLIB 距离规则计算。

| 统计公式 |
| :--- |
| $\displaystyle \mathrm{distance\_cv} = \frac{\sigma\left(\{d_{ij} \mid 1 \le i < j \le n\}\right)}{\mu\left(\{d_{ij} \mid 1 \le i < j \le n\}\right)}$ |
| $\displaystyle \mathrm{nn\_cv} = \frac{\sigma\left(\{\min_{j \ne i} d_{ij} \mid 1 \le i \le n\}\right)}{\mu\left(\{\min_{j \ne i} d_{ij} \mid 1 \le i \le n\}\right)}$ |

- $d_{ij}$ 表示节点 $i$ 和节点 $j$ 之间按 TSPLIB 规则计算得到的距离，$n$ 表示节点数量。
- $\mu(S)$ 表示集合 $S$ 中数值的算术平均值，$\sigma(S)$ 表示集合 $S$ 中数值的标准差。
- `distance_cv` 是所有无向节点对距离的变异系数，数值越大表示全局距离尺度越不均匀。
- `nn_cv` 是每个节点最近邻距离的变异系数，数值越大表示局部稀疏/密集差异越明显，通常意味着局部结构更不均衡。

<!-- tsplib-stat-formulas:end -->

### smoke

- `tsplib_burma14`
  - 问题描述：14 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=14`
  - 参考值：`objective=3323`
  - 数据特征：小规模 `GEO` 地理距离实例，用于验证地理坐标解析和距离公式。
  - 统计特征：`distance_cv=0.5301`，`nn_cv=0.7599`
- `tsplib_ulysses22`
  - 问题描述：22 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=22`
  - 参考值：`objective=7013`
  - 数据特征：小规模 `GEO` 实例，距离分布不均匀，补充地理坐标 sanity 样本。
  - 统计特征：`distance_cv=0.7158`，`nn_cv=1.6292`
- `tsplib_bayg29`
  - 问题描述：29 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=29`
  - 参考值：`objective=1610`
  - 数据特征：小规模 `EXPLICIT/UPPER_ROW` 显式矩阵，验证非坐标型 TSP 数据。
  - 统计特征：`distance_cv=0.4694`，`nn_cv=0.2788`
- `tsplib_att48`
  - 问题描述：48 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=48`
  - 参考值：`objective=10628`
  - 数据特征：`ATT` pseudo-Euclidean 距离，小规模但距离尺度和普通欧氏样本不同。
  - 统计特征：`distance_cv=0.5930`，`nn_cv=0.5030`
- `tsplib_gr48`
  - 问题描述：48 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=48`
  - 参考值：`objective=5046`
  - 数据特征：`EXPLICIT/LOWER_DIAG_ROW` 显式矩阵，补充三角矩阵格式覆盖。
  - 统计特征：`distance_cv=0.4860`，`nn_cv=0.4630`
- `tsplib_eil51`
  - 问题描述：51 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=51`
  - 参考值：`objective=426`
  - 数据特征：经典 `EUC_2D` 小规模紧凑平面点集，适合快速 smoke。
  - 统计特征：`distance_cv=0.4653`，`nn_cv=0.2623`
- `tsplib_berlin52`
  - 问题描述：52 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=52`
  - 参考值：`objective=7542`
  - 数据特征：经典 `EUC_2D` 实例，节点分布较不均匀，是已有基准样本。
  - 统计特征：`distance_cv=0.5908`，`nn_cv=0.7809`
- `tsplib_st70`
  - 问题描述：70 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=70`
  - 参考值：`objective=675`
  - 数据特征：小规模 `EUC_2D` 均衡平面样本，目标值尺度较小。
  - 统计特征：`distance_cv=0.4667`，`nn_cv=0.4944`
- `tsplib_pr76`
  - 问题描述：76 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=76`
  - 参考值：`objective=108159`
  - 数据特征：PR 系列小规模代表，坐标尺度大，和 EIL/ST 样本形成对照。
  - 统计特征：`distance_cv=0.5178`，`nn_cv=0.6218`
- `tsplib_kroa100`
  - 问题描述：100 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=100`
  - 参考值：`objective=21282`
  - 数据特征：KRO 100 系列代表，`EUC_2D` 随机平面散点；同系列 `kroB/C/D/E100` 近似度较高，因此保留一个代表。
  - 统计特征：`distance_cv=0.5355`，`nn_cv=0.5430`

### calibration

- `tsplib_eil101`
  - 问题描述：101 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=101`
  - 参考值：`objective=629`
  - 数据特征：EIL 系列中型延伸，紧凑平面点集，适合观察轻量预算质量变化。
  - 统计特征：`distance_cv=0.4821`，`nn_cv=0.4294`
- `tsplib_ch130`
  - 问题描述：130 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=130`
  - 参考值：`objective=6110`
  - 数据特征：均衡 `EUC_2D` 散点结构，补充 100-150 节点校准样本。
  - 统计特征：`distance_cv=0.4772`，`nn_cv=0.5586`
- `tsplib_kroa150`
  - 问题描述：150 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=150`
  - 参考值：`objective=26524`
  - 数据特征：KRO 中型代表，和 `kroa100` 构成同系列规模梯度。
  - 统计特征：`distance_cv=0.5351`，`nn_cv=0.5626`
- `tsplib_pr152`
  - 问题描述：152 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=152`
  - 参考值：`objective=73682`
  - 数据特征：PR 中型代表，坐标尺度较大，近邻距离差异明显。
  - 统计特征：`distance_cv=0.5305`，`nn_cv=0.7241`
- `tsplib_rat195`
  - 问题描述：195 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=195`
  - 参考值：`objective=2323`
  - 数据特征：RAT 系列中型代表，局部密度变化适中，目标值尺度较小。
  - 统计特征：`distance_cv=0.5488`，`nn_cv=0.1917`
- `tsplib_ts225`
  - 问题描述：225 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=225`
  - 参考值：`objective=126643`
  - 数据特征：`EUC_2D` 规则结构较强，近邻距离较稳定，用作结构对照。
  - 统计特征：`distance_cv=0.4692`，`nn_cv=0.0000`
- `tsplib_gil262`
  - 问题描述：262 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=262`
  - 参考值：`objective=2378`
  - 数据特征：紧凑平面散点，节点数接近 `a280` 但坐标尺度和目标值不同。
  - 统计特征：`distance_cv=0.4734`，`nn_cv=0.5460`
- `tsplib_a280`
  - 问题描述：280 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=280`
  - 参考值：`objective=2579`
  - 数据特征：经典 `EUC_2D` 中型样本，当前已有 case，轻预算下表现较稳定。
  - 统计特征：`distance_cv=0.5141`，`nn_cv=0.1742`
- `tsplib_lin318`
  - 问题描述：318 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=318`
  - 参考值：`objective=42029`
  - 数据特征：Lin/Kernighan 经典实例；`linhp318` 与其坐标重复，因此只保留 `lin318`。
  - 统计特征：`distance_cv=0.4878`，`nn_cv=0.6933`
- `tsplib_rd400`
  - 问题描述：400 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=400`
  - 参考值：`objective=15281`
  - 数据特征：随机分布型 `EUC_2D` 样本，补充 calibration 上沿。
  - 统计特征：`distance_cv=0.4737`，`nn_cv=0.5333`
- `tsplib_gr431`
  - 问题描述：431 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=431`
  - 参考值：`objective=171414`
  - 数据特征：中型 `GEO` 地理距离代表，搜索结构不同于平面欧氏实例。
  - 统计特征：`distance_cv=0.7544`，`nn_cv=1.1702`
- `tsplib_pcb442`
  - 问题描述：442 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=442`
  - 参考值：`objective=50778`
  - 数据特征：PCB 布局类 `EUC_2D` 点集，作为 calibration 上沿的工程布局样本。
  - 统计特征：`distance_cv=0.4752`，`nn_cv=0.2389`

### full

- `tsplib_att532`
  - 问题描述：532 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=532`
  - 参考值：`objective=27686`
  - 数据特征：`ATT` 中大样本，保留 pseudo-Euclidean 距离在 full 层的覆盖。
  - 统计特征：`distance_cv=0.6608`，`nn_cv=0.7320`
- `tsplib_si535`
  - 问题描述：535 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=535`
  - 参考值：`objective=48450`
  - 数据特征：`EXPLICIT/UPPER_DIAG_ROW` 显式矩阵，补充非坐标型 full 样本。
  - 统计特征：`distance_cv=0.3515`，`nn_cv=0.1606`
- `tsplib_u574`
  - 问题描述：574 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=574`
  - 参考值：`objective=36905`
  - 数据特征：U 系列 full 下沿代表，矩形平面散点。
  - 统计特征：`distance_cv=0.5305`，`nn_cv=0.5464`
- `tsplib_rat575`
  - 问题描述：575 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=575`
  - 参考值：`objective=6773`
  - 数据特征：RAT full 下沿样本，实测 10 秒预算基本可控。
  - 统计特征：`distance_cv=0.5451`，`nn_cv=0.3286`
- `tsplib_p654`
  - 问题描述：654 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=654`
  - 参考值：`objective=34643`
  - 数据特征：距离分布更不均匀，局部结构差异较大，补充 full 层难度变化。
  - 统计特征：`distance_cv=0.5891`，`nn_cv=2.0572`
- `tsplib_d657`
  - 问题描述：657 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=657`
  - 参考值：`objective=48912`
  - 数据特征：D 系列 full 代表，近邻距离差异高，和 RAT/U 系列不同。
  - 统计特征：`distance_cv=0.4954`，`nn_cv=1.1063`
- `tsplib_gr666`
  - 问题描述：666 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=666`
  - 参考值：`objective=294358`
  - 数据特征：full 层 `GEO` 地理距离代表，补充非欧氏坐标样本。
  - 统计特征：`distance_cv=0.5803`，`nn_cv=1.0925`
- `tsplib_u724`
  - 问题描述：724 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=724`
  - 参考值：`objective=41910`
  - 数据特征：U 系列中等 full 代表，和 `u574` 构成规模梯度。
  - 统计特征：`distance_cv=0.5235`，`nn_cv=0.5044`
- `tsplib_rat783`
  - 问题描述：783 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=783`
  - 参考值：`objective=8806`
  - 数据特征：RAT 系列更大样本，保留局部密度结构的规模变化。
  - 统计特征：`distance_cv=0.5434`，`nn_cv=0.4166`
- `tsplib_dsj1000`
  - 问题描述：1000 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=1000`
  - 参考值：`objective=18660188`
  - 数据特征：`CEIL_2D` 聚类随机问题，作为 full 上沿压力样本。
  - 统计特征：`distance_cv=0.5139`，`nn_cv=0.7453`

### pressure

- `tsplib_pr1002`
  - 问题描述：1002 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=1002`
  - 参考值：`objective=259045`
  - 数据特征：pressure 下沿 PR 系列代表，规模刚超过 full 上限。
  - 统计特征：`distance_cv=0.4912`，`nn_cv=0.4778`
- `tsplib_si1032`
  - 问题描述：1032 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=1032`
  - 参考值：`objective=92650`
  - 数据特征：`EXPLICIT/UPPER_DIAG_ROW` 大显式矩阵，补充 pressure 层非坐标型样本。
  - 统计特征：`distance_cv=0.3547`，`nn_cv=0.0653`
- `tsplib_u1060`
  - 问题描述：1060 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=1060`
  - 参考值：`objective=224094`
  - 数据特征：U 系列千点级代表，坐标尺度较大。
  - 统计特征：`distance_cv=0.5689`，`nn_cv=0.7189`
- `tsplib_vm1084`
  - 问题描述：1084 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=1084`
  - 参考值：`objective=239297`
  - 数据特征：VM 系列代表，坐标分布和尺度不同于 U/PR/PCB。
  - 统计特征：`distance_cv=0.5247`，`nn_cv=0.8047`
- `tsplib_pcb1173`
  - 问题描述：1173 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=1173`
  - 参考值：`objective=56892`
  - 数据特征：PCB 千点级布局样本，补充工程布局类 pressure 数据。
  - 统计特征：`distance_cv=0.4996`，`nn_cv=0.3285`
- `tsplib_rl1304`
  - 问题描述：1304 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=1304`
  - 参考值：`objective=252948`
  - 数据特征：RL 系列代表，实测对 GA 预算较重，适合作 pressure 层性能观察。
  - 统计特征：`distance_cv=0.5106`，`nn_cv=0.6308`
- `tsplib_u2152`
  - 问题描述：2152 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=2152`
  - 参考值：`objective=64253`
  - 数据特征：U 系列高规模代表，距离分布更不均匀，用于替换较轻的 `u1432`。
  - 统计特征：`distance_cv=0.5207`，`nn_cv=0.0861`
- `tsplib_fl1577`
  - 问题描述：1577 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=1577`
  - 参考值：`objective=22249`
  - 数据特征：FL 系列 pressure 代表，局部结构差异明显。
  - 统计特征：`distance_cv=0.5441`，`nn_cv=0.2045`
- `tsplib_d1655`
  - 问题描述：1655 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=1655`
  - 参考值：`objective=62128`
  - 数据特征：D 系列 pressure 样本，局部近邻距离差异更高，实测 GA 搜索质量压力明显，和 `d2103` 共同保留而非互相替代。
  - 统计特征：`distance_cv=0.4861`，`nn_cv=1.2137`
- `tsplib_d2103`
  - 问题描述：2103 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=2103`
  - 参考值：`objective=80450`
  - 数据特征：D 系列 2000 节点级 pressure 代表，保留同系列结构并提升压力。
  - 统计特征：`distance_cv=0.4860`，`nn_cv=0.7358`
- `tsplib_pr2392`
  - 问题描述：2392 城市对称 TSP，目标是最小化 Hamiltonian 回路长度。
  - 规模：`nodes=2392`
  - 参考值：`objective=378032`
  - 数据特征：PR 大样本，作为超过 2000 节点的特例保留；实测耗时明显偏重，不宜作为普通 smoke。
  - 统计特征：`distance_cv=0.4903`，`nn_cv=0.3722`

## 问题定义

每个 case 都是在给定城市集合和 TSPLIB 距离度量的前提下，寻找一条最短 Hamiltonian 回路。当前 benchmark 默认使用 `sequence_var` 表示访问顺序，并通过 `external_call` 或图式转移代价计算整条回路长度。正式运行时应优先使用 `--no-download` 读取本地 `tsp/raw/` 中的已缓存数据。