# TSPLIB

## 数据来源说明

TSPLIB 是经典旅行商问题实例库，用于评估路由顺序优化算法。

数据集来源：

- TSPLIB95 主页：https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/
- TSP 实例归档：https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/
- 对称 TSP 参考解：https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/STSP.html
- 本地原始数据：benchmarks/cases/tsplib/tsp/raw/ALL_tsp/

## 问题说明

TSPLIB 对称 TSP 要求每个城市恰好访问一次并回到起点，在给定的距离度量下最小化 Hamiltonian 回路总长度。

## 数据筛选依据

- 数规模定义：规模以节点数 nodes 定义，也可理解为城市数。
- tier 范围：按注册数据统计，以 nodes 为主要分层指标： smoke=14-100，calibration=101-442，full=532-1000，pressure=1002-2392。
- 筛选策略：筛选策略综合考虑规模、距离类型、显式距离矩阵格式和节点几何结构，同系列中去除非常近似的算例，保留不同规模和结构的代表。

## 建模说明

使用 sequence_var 表示访问顺序，使用 sequence_transition_sum 累加闭回路边代价；可选外部回调风格计算路径长度。

- 适用的求解方式：solve() 适用；solve_cpsat() 和 solve_milp() 当前不适用，因为当前模型没有提供对应的 CPSAT/MILP lowering。

## 特殊备注

TSPLIB 包含 EUC_2D、CEIL_2D、ATT、GEO 和 EXPLICIT 等距离类型，距离计算必须遵循各自的 TSPLIB 规则；当前参考值均为对称 TSP 的已知最优值。

## 相关 case

### smoke

- `tsplib_burma14`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=14`
  - 参考值：最优
  - 参考值/区间：`objective=3323`
  - 备注：无
- `tsplib_ulysses22`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=22`
  - 参考值：最优
  - 参考值/区间：`objective=7013`
  - 备注：无
- `tsplib_bayg29`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=29`
  - 参考值：最优
  - 参考值/区间：`objective=1610`
  - 备注：无
- `tsplib_att48`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=48`
  - 参考值：最优
  - 参考值/区间：`objective=10628`
  - 备注：无
- `tsplib_gr48`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=48`
  - 参考值：最优
  - 参考值/区间：`objective=5046`
  - 备注：无
- `tsplib_eil51`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=51`
  - 参考值：最优
  - 参考值/区间：`objective=426`
  - 备注：无
- `tsplib_berlin52`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=52`
  - 参考值：最优
  - 参考值/区间：`objective=7542`
  - 备注：无
- `tsplib_st70`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=70`
  - 参考值：最优
  - 参考值/区间：`objective=675`
  - 备注：无
- `tsplib_pr76`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=76`
  - 参考值：最优
  - 参考值/区间：`objective=108159`
  - 备注：无
- `tsplib_kroa100`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=100`
  - 参考值：最优
  - 参考值/区间：`objective=21282`
  - 备注：无

### calibration

- `tsplib_eil101`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=101`
  - 参考值：最优
  - 参考值/区间：`objective=629`
  - 备注：无
- `tsplib_ch130`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=130`
  - 参考值：最优
  - 参考值/区间：`objective=6110`
  - 备注：无
- `tsplib_kroa150`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=150`
  - 参考值：最优
  - 参考值/区间：`objective=26524`
  - 备注：无
- `tsplib_pr152`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=152`
  - 参考值：最优
  - 参考值/区间：`objective=73682`
  - 备注：无
- `tsplib_rat195`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=195`
  - 参考值：最优
  - 参考值/区间：`objective=2323`
  - 备注：无
- `tsplib_ts225`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=225`
  - 参考值：最优
  - 参考值/区间：`objective=126643`
  - 备注：无
- `tsplib_gil262`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=262`
  - 参考值：最优
  - 参考值/区间：`objective=2378`
  - 备注：无
- `tsplib_a280`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=280`
  - 参考值：最优
  - 参考值/区间：`objective=2579`
  - 备注：无
- `tsplib_lin318`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=318`
  - 参考值：最优
  - 参考值/区间：`objective=42029`
  - 备注：无
- `tsplib_rd400`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=400`
  - 参考值：最优
  - 参考值/区间：`objective=15281`
  - 备注：无
- `tsplib_gr431`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=431`
  - 参考值：最优
  - 参考值/区间：`objective=171414`
  - 备注：无
- `tsplib_pcb442`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=442`
  - 参考值：最优
  - 参考值/区间：`objective=50778`
  - 备注：无

### full

- `tsplib_att532`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=532`
  - 参考值：最优
  - 参考值/区间：`objective=27686`
  - 备注：无
- `tsplib_si535`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=535`
  - 参考值：最优
  - 参考值/区间：`objective=48450`
  - 备注：无
- `tsplib_u574`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=574`
  - 参考值：最优
  - 参考值/区间：`objective=36905`
  - 备注：无
- `tsplib_rat575`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=575`
  - 参考值：最优
  - 参考值/区间：`objective=6773`
  - 备注：无
- `tsplib_p654`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=654`
  - 参考值：最优
  - 参考值/区间：`objective=34643`
  - 备注：无
- `tsplib_d657`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=657`
  - 参考值：最优
  - 参考值/区间：`objective=48912`
  - 备注：无
- `tsplib_gr666`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=666`
  - 参考值：最优
  - 参考值/区间：`objective=294358`
  - 备注：无
- `tsplib_u724`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=724`
  - 参考值：最优
  - 参考值/区间：`objective=41910`
  - 备注：无
- `tsplib_rat783`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=783`
  - 参考值：最优
  - 参考值/区间：`objective=8806`
  - 备注：无
- `tsplib_dsj1000`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=1000`
  - 参考值：最优
  - 参考值/区间：`objective=18660188`
  - 备注：无

### pressure

- `tsplib_pr1002`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=1002`
  - 参考值：最优
  - 参考值/区间：`objective=259045`
  - 备注：无
- `tsplib_si1032`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=1032`
  - 参考值：最优
  - 参考值/区间：`objective=92650`
  - 备注：无
- `tsplib_u1060`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=1060`
  - 参考值：最优
  - 参考值/区间：`objective=224094`
  - 备注：无
- `tsplib_vm1084`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=1084`
  - 参考值：最优
  - 参考值/区间：`objective=239297`
  - 备注：无
- `tsplib_pcb1173`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=1173`
  - 参考值：最优
  - 参考值/区间：`objective=56892`
  - 备注：无
- `tsplib_rl1304`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=1304`
  - 参考值：最优
  - 参考值/区间：`objective=252948`
  - 备注：无
- `tsplib_fl1577`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=1577`
  - 参考值：最优
  - 参考值/区间：`objective=22249`
  - 备注：无
- `tsplib_d1655`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=1655`
  - 参考值：最优
  - 参考值/区间：`objective=62128`
  - 备注：无
- `tsplib_d2103`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=2103`
  - 参考值：最优
  - 参考值/区间：`objective=80450`
  - 备注：无
- `tsplib_u2152`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=2152`
  - 参考值：最优
  - 参考值/区间：`objective=64253`
  - 备注：无
- `tsplib_pr2392`
  - 问题描述：对称 TSP，最小化 Hamiltonian 回路总长度。
  - 规模：`nodes=2392`
  - 参考值：最优
  - 参考值/区间：`objective=378032`
  - 备注：无

共 43 个 case。
