# CVRPLIB 数据来源说明

CVRPLIB 目录保存来自 CVRPLIB 的 capacitated vehicle routing benchmark case。当前筛选的是 CVRP（Capacitated Vehicle Routing Problem，带容量约束车辆路径问题）实例，用于后续测试 OptAgent 在多路线、容量约束和 routing 序列优化问题上的表现。

数据集来源：

- CVRPLIB 主页：https://vrp.atd-lab.inf.puc-rio.br/index.php/en/
- CVRP 实例页：https://galgos.inf.puc-rio.br/cvrplib/index.php/en/instances
- 本地完整数据缓存：`benchmarks/cases/cvrplib/cvrp/raw/cvrp_instances/`
- 正式筛选 case：`benchmarks/cases/cvrplib/cvrp/raw/` 根层的 `.vrp`、`.sol` 和 `.json` 文件

筛选后的正式候选 case 会复制到 `cvrp/raw/` 根层，保证 `--no-download` 时可以直接读取。`.vrp` 文件保留 CVRPLIB 原始格式，`.sol` 文件保留来源提供的参考解，`.json` 文件是 benchmark loader 后续使用的结构化格式。

当前 `cvrplib/cvrp` 统一按固定车辆数的 CVRP 口径处理：`size.vehicles` 是输入侧车辆数，目标是在该固定车辆数下最小化总路线距离。对 XML100、Golden、Tai 和 Li 中原始 `.vrp` 未显式给出车辆数的选中算例，`size.vehicles` 已固定为对应参考解 `.sol` 的路线数。原始 XML 系列中不固定车辆数、需要同时权衡车辆数和距离的特殊口径，单独放入 `cvrp2lib/cvrp_xml` 数据集维护。

## JSON 数据格式说明

当前结构化文件为 `cvrp/raw/<instance>.json`。每个 JSON 文件包含：

- `name`：CVRPLIB 实例名。
- `problem_type`：问题类型，当前为 `CVRP`。
- `source` 和 `series`：数据来源和实例系列。
- `metadata`：原始注释、距离类型和原始 `.vrp` 文件名。
- `size`：规模信息，包括 `nodes`、`customers`、`vehicles`、`capacity`、`directed_arcs`。
- `depot`：仓库节点 id，保留原始 CVRPLIB 节点编号。
- `nodes`：节点列表，每个节点包含 `id`、`x`、`y`、`demand`、`is_depot`。
- `statistics`：筛选和后续分析用统计量，包括总需求、容量下界、需求变异系数、距离变异系数、最近邻变异系数、仓库距离变异系数、长宽比和空间密度。
- `tier`：当前 benchmark 分层，取值为 `smoke`、`calibration`、`full` 或 `pressure`。
- `reference`：当前正式筛选 case 均包含 `.sol` 对应的参考解，字段包含 best-known 或 optimal `objective`、路线、路线数、状态和来源文件。

注意：`.sol` 文件中的路线使用 CVRPLIB 解文件的客户编号口径，路线中省略 depot；`.json` 中的 `nodes[].id` 保留 `.vrp` 原始节点编号。后续 loader 如需校验参考解，应显式处理这两个编号口径。

## 数据筛选依据

本轮处于算例筛选阶段，先按规模划分四个 tier，再用算例特征去除高度近似实例。CVRP 的主规模使用 `customers = DIMENSION - 1`，文档展示时同时保留 `nodes = DIMENSION`。tier 范围为：

- `smoke`：`nodes=16-80`
- `calibration`：`nodes=81-200`
- `full`：`nodes=201-500`
- `pressure`：`nodes=501-1200`

相似度特征包含：规模、车辆数、容量、总需求、容量路线下界、需求密度、车辆比例、需求变异系数、全局距离变异系数、最近邻距离变异系数、仓库距离变异系数、坐标长宽比和空间密度。对大尺度数值取 `log1p` 后做 z-score 标准化，再用加权欧氏距离比较。验证时，`nodes <= 1200` 的候选样本最近邻来自同一 series 的比例为 `0.996`，最近对主要是 CMT 成对实例和 XML 生成族近邻，说明该方案能识别结构高度相似的样本。

筛选策略优先保留经典 A/B/P/E/F/CMT/M/tai/Golden/X/DIMACS/Li/XL 系列，再从 XML 生成族中补充 calibration 层的结构差异样本，避免 10000 个 XML 实例淹没其它来源。

## 建模说明

## 相关 case

### smoke

- `cvrplib_P-n16-k8`
  - 问题描述：CVRPLIB CVRP 实例 `P-n16-k8`，从一个 depot 出发为 `15` 个客户设计容量受限车辆路线，目标是在固定车辆数 `8` 下最小化总路线距离。
  - 规模：`nodes=16`，`customers=15`，`vehicles=8`，`capacity=35`，`directed_arcs=240`
  - 参考值：`objective=450`
  - 数据特征：`P` series，容量下界 `route_lb=8`，总需求 `total_demand=246`。
  - 统计特征：`demand_cv=0.4963`，`distance_cv=0.4788`，`nn_cv=0.1186`，`depot_distance_cv=0.2531`

- `cvrplib_P-n19-k2`
  - 问题描述：CVRPLIB CVRP 实例 `P-n19-k2`，从一个 depot 出发为 `18` 个客户设计容量受限车辆路线，目标是在固定车辆数 `2` 下最小化总路线距离。
  - 规模：`nodes=19`，`customers=18`，`vehicles=2`，`capacity=160`，`directed_arcs=342`
  - 参考值：`objective=212`
  - 数据特征：`P` series，容量下界 `route_lb=2`，总需求 `total_demand=310`。
  - 统计特征：`demand_cv=0.4352`，`distance_cv=0.4636`，`nn_cv=0.1893`，`depot_distance_cv=0.3144`

- `cvrplib_E-n22-k4`
  - 问题描述：CVRPLIB CVRP 实例 `E-n22-k4`，从一个 depot 出发为 `21` 个客户设计容量受限车辆路线，目标是在固定车辆数 `4` 下最小化总路线距离。
  - 规模：`nodes=22`，`customers=21`，`vehicles=4`，`capacity=6000`，`directed_arcs=462`
  - 参考值：`objective=375`
  - 数据特征：`E` series，容量下界 `route_lb=4`，总需求 `total_demand=22500`。
  - 统计特征：`demand_cv=0.574`，`distance_cv=0.4919`，`nn_cv=0.4021`，`depot_distance_cv=0.416`

- `cvrplib_E-n23-k3`
  - 问题描述：CVRPLIB CVRP 实例 `E-n23-k3`，从一个 depot 出发为 `22` 个客户设计容量受限车辆路线，目标是在固定车辆数 `3` 下最小化总路线距离。
  - 规模：`nodes=23`，`customers=22`，`vehicles=3`，`capacity=4500`，`directed_arcs=506`
  - 参考值：`objective=569`
  - 数据特征：`E` series，容量下界 `route_lb=3`，总需求 `total_demand=10189`。
  - 统计特征：`demand_cv=1.786`，`distance_cv=0.5008`，`nn_cv=0.6719`，`depot_distance_cv=0.3778`

- `cvrplib_B-n31-k5`
  - 问题描述：CVRPLIB CVRP 实例 `B-n31-k5`，从一个 depot 出发为 `30` 个客户设计容量受限车辆路线，目标是在固定车辆数 `5` 下最小化总路线距离。
  - 规模：`nodes=31`，`customers=30`，`vehicles=5`，`capacity=100`，`directed_arcs=930`
  - 参考值：`objective=672`
  - 数据特征：`B` series，容量下界 `route_lb=5`，总需求 `total_demand=412`。
  - 统计特征：`demand_cv=0.4357`，`distance_cv=0.9126`，`nn_cv=0.7408`，`depot_distance_cv=0.2763`

- `cvrplib_E-n31-k7`
  - 问题描述：CVRPLIB CVRP 实例 `E-n31-k7`，从一个 depot 出发为 `30` 个客户设计容量受限车辆路线，目标是在固定车辆数 `7` 下最小化总路线距离。
  - 规模：`nodes=31`，`customers=30`，`vehicles=7`，`capacity=140`，`directed_arcs=930`
  - 参考值：`objective=379`
  - 数据特征：`E` series，容量下界 `route_lb=7`，总需求 `total_demand=903`。
  - 统计特征：`demand_cv=1.001`，`distance_cv=0`，`nn_cv=0`，`depot_distance_cv=0`

- `cvrplib_A-n32-k5`
  - 问题描述：CVRPLIB CVRP 实例 `A-n32-k5`，从一个 depot 出发为 `31` 个客户设计容量受限车辆路线，目标是在固定车辆数 `5` 下最小化总路线距离。
  - 规模：`nodes=32`，`customers=31`，`vehicles=5`，`capacity=100`，`directed_arcs=992`
  - 参考值：`objective=784`
  - 数据特征：`A` series，容量下界 `route_lb=5`，总需求 `total_demand=410`。
  - 统计特征：`demand_cv=0.5397`，`distance_cv=0.465`，`nn_cv=0.6143`，`depot_distance_cv=0.4162`

- `cvrplib_B-n34-k5`
  - 问题描述：CVRPLIB CVRP 实例 `B-n34-k5`，从一个 depot 出发为 `33` 个客户设计容量受限车辆路线，目标是在固定车辆数 `5` 下最小化总路线距离。
  - 规模：`nodes=34`，`customers=33`，`vehicles=5`，`capacity=100`，`directed_arcs=1122`
  - 参考值：`objective=788`
  - 数据特征：`B` series，容量下界 `route_lb=5`，总需求 `total_demand=457`。
  - 统计特征：`demand_cv=1.1089`，`distance_cv=0.6754`，`nn_cv=1.3888`，`depot_distance_cv=0.1756`

- `cvrplib_B-n38-k6`
  - 问题描述：CVRPLIB CVRP 实例 `B-n38-k6`，从一个 depot 出发为 `37` 个客户设计容量受限车辆路线，目标是在固定车辆数 `6` 下最小化总路线距离。
  - 规模：`nodes=38`，`customers=37`，`vehicles=6`，`capacity=100`，`directed_arcs=1406`
  - 参考值：`objective=805`
  - 数据特征：`B` series，容量下界 `route_lb=6`，总需求 `total_demand=512`。
  - 统计特征：`demand_cv=0.5218`，`distance_cv=0.609`，`nn_cv=1.0161`，`depot_distance_cv=0.3752`

- `cvrplib_B-n45-k5`
  - 问题描述：CVRPLIB CVRP 实例 `B-n45-k5`，从一个 depot 出发为 `44` 个客户设计容量受限车辆路线，目标是在固定车辆数 `5` 下最小化总路线距离。
  - 规模：`nodes=45`，`customers=44`，`vehicles=5`，`capacity=100`，`directed_arcs=1980`
  - 参考值：`objective=751`
  - 数据特征：`B` series，容量下界 `route_lb=5`，总需求 `total_demand=486`。
  - 统计特征：`demand_cv=0.656`，`distance_cv=0.5246`，`nn_cv=1.356`，`depot_distance_cv=0.4168`

- `cvrplib_F-n45-k4`
  - 问题描述：CVRPLIB CVRP 实例 `F-n45-k4`，从一个 depot 出发为 `44` 个客户设计容量受限车辆路线，目标是在固定车辆数 `4` 下最小化总路线距离。
  - 规模：`nodes=45`，`customers=44`，`vehicles=4`，`capacity=2010`，`directed_arcs=1980`
  - 参考值：`objective=724`
  - 数据特征：`F` series，容量下界 `route_lb=4`，总需求 `total_demand=7220`。
  - 统计特征：`demand_cv=1.5576`，`distance_cv=0.6044`，`nn_cv=1.9849`，`depot_distance_cv=0.6366`

- `cvrplib_P-n55-k15`
  - 问题描述：CVRPLIB CVRP 实例 `P-n55-k15`，从一个 depot 出发为 `54` 个客户设计容量受限车辆路线，目标是在固定车辆数 `15` 下最小化总路线距离。
  - 规模：`nodes=55`，`customers=54`，`vehicles=15`，`capacity=70`，`directed_arcs=2970`
  - 参考值：`objective=989`
  - 数据特征：`P` series，容量下界 `route_lb=15`，总需求 `total_demand=1042`。
  - 统计特征：`demand_cv=0.3629`，`distance_cv=0.4605`，`nn_cv=0.32`，`depot_distance_cv=0.3755`

- `cvrplib_B-n56-k7`
  - 问题描述：CVRPLIB CVRP 实例 `B-n56-k7`，从一个 depot 出发为 `55` 个客户设计容量受限车辆路线，目标是在固定车辆数 `7` 下最小化总路线距离。
  - 规模：`nodes=56`，`customers=55`，`vehicles=7`，`capacity=100`，`directed_arcs=3080`
  - 参考值：`objective=707`
  - 数据特征：`B` series，容量下界 `route_lb=7`，总需求 `total_demand=616`。
  - 统计特征：`demand_cv=0.6114`，`distance_cv=0.6228`，`nn_cv=0.6911`，`depot_distance_cv=0.6733`

- `cvrplib_F-n72-k4`
  - 问题描述：CVRPLIB CVRP 实例 `F-n72-k4`，从一个 depot 出发为 `71` 个客户设计容量受限车辆路线，目标是在固定车辆数 `4` 下最小化总路线距离。
  - 规模：`nodes=72`，`customers=71`，`vehicles=4`，`capacity=30000`，`directed_arcs=5112`
  - 参考值：`objective=237`
  - 数据特征：`F` series，容量下界 `route_lb=4`，总需求 `total_demand=114840`。
  - 统计特征：`demand_cv=1.8472`，`distance_cv=0.5616`，`nn_cv=0.6837`，`depot_distance_cv=0.3579`

- `cvrplib_P-n76-k4`
  - 问题描述：CVRPLIB CVRP 实例 `P-n76-k4`，从一个 depot 出发为 `75` 个客户设计容量受限车辆路线，目标是在固定车辆数 `4` 下最小化总路线距离。
  - 规模：`nodes=76`，`customers=75`，`vehicles=4`，`capacity=350`，`directed_arcs=5700`
  - 参考值：`objective=593`
  - 数据特征：`P` series，容量下界 `route_lb=4`，总需求 `total_demand=1364`。
  - 统计特征：`demand_cv=0.4348`，`distance_cv=0.4723`，`nn_cv=0.3075`，`depot_distance_cv=0.4167`

- `cvrplib_Tai75a`
  - 问题描述：CVRPLIB CVRP 实例 `Tai75a`，从一个 depot 出发为 `75` 个客户设计容量受限车辆路线，目标是在固定车辆数 `10` 下最小化总路线距离。
  - 规模：`nodes=76`，`customers=75`，`vehicles=10`，`capacity=1445`，`directed_arcs=5700`
  - 参考值：`objective=1618.36`
  - 数据特征：`Tai75a` series，容量下界 `route_lb=10`，总需求 `total_demand=13756`。
  - 统计特征：`demand_cv=1.3246`，`distance_cv=0.5949`，`nn_cv=0.5995`，`depot_distance_cv=0.4362`

- `cvrplib_Tai75b`
  - 问题描述：CVRPLIB CVRP 实例 `Tai75b`，从一个 depot 出发为 `75` 个客户设计容量受限车辆路线，目标是在固定车辆数 `10` 下最小化总路线距离。
  - 规模：`nodes=76`，`customers=75`，`vehicles=10`，`capacity=1679`，`directed_arcs=5700`
  - 参考值：`objective=1344.62`
  - 数据特征：`Tai75b` series，容量下界 `route_lb=9`，总需求 `total_demand=14906`。
  - 统计特征：`demand_cv=1.3759`，`distance_cv=0.6948`，`nn_cv=1.289`，`depot_distance_cv=0.7983`


### calibration

- `cvrplib_E-n101-k14`
  - 问题描述：CVRPLIB CVRP 实例 `E-n101-k14`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线，目标是在固定车辆数 `14` 下最小化总路线距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=14`，`capacity=112`，`directed_arcs=10100`
  - 参考值：`objective=1067`
  - 数据特征：`E` series，容量下界 `route_lb=14`，总需求 `total_demand=1458`。
  - 统计特征：`demand_cv=0.6054`，`distance_cv=0.4803`，`nn_cv=0.4151`，`depot_distance_cv=0.3802`

- `cvrplib_Tai100c`
  - 问题描述：CVRPLIB CVRP 实例 `Tai100c`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线，目标是在固定车辆数 `11` 下最小化总路线距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=11`，`capacity=2043`，`directed_arcs=10100`
  - 参考值：`objective=1406.2`
  - 数据特征：`Tai100c` series，容量下界 `route_lb=11`，总需求 `total_demand=20999`。
  - 统计特征：`demand_cv=1.3565`，`distance_cv=0.6838`，`nn_cv=1.3136`，`depot_distance_cv=0.8174`

- `cvrplib_XML100_1111_04`
  - 问题描述：CVRPLIB CVRP 实例 `XML100_1111_04`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线，目标是在固定车辆数 `34` 下最小化总路线距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=34`，`capacity=3`，`directed_arcs=10100`
  - 参考值：`objective=37554`
  - 数据特征：`XML100` series，容量下界 `route_lb=34`，总需求 `total_demand=100`。
  - 统计特征：`demand_cv=0`，`distance_cv=0.4745`，`nn_cv=0.4852`，`depot_distance_cv=0.4634`

- `cvrplib_XML100_1211_01`
  - 问题描述：CVRPLIB CVRP 实例 `XML100_1211_01`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线，目标是在固定车辆数 `34` 下最小化总路线距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=34`，`capacity=3`，`directed_arcs=10100`
  - 参考值：`objective=44590`
  - 数据特征：`XML100` series，容量下界 `route_lb=34`，总需求 `total_demand=100`。
  - 统计特征：`demand_cv=0`，`distance_cv=0.6307`，`nn_cv=1.3269`，`depot_distance_cv=0.221`

- `cvrplib_XML100_1211_02`
  - 问题描述：CVRPLIB CVRP 实例 `XML100_1211_02`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线，目标是在固定车辆数 `34` 下最小化总路线距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=34`，`capacity=3`，`directed_arcs=10100`
  - 参考值：`objective=59187`
  - 数据特征：`XML100` series，容量下界 `route_lb=34`，总需求 `total_demand=100`。
  - 统计特征：`demand_cv=0`，`distance_cv=0.7125`，`nn_cv=0.9381`，`depot_distance_cv=0.0998`

- `cvrplib_XML100_1211_10`
  - 问题描述：CVRPLIB CVRP 实例 `XML100_1211_10`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线，目标是在固定车辆数 `34` 下最小化总路线距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=34`，`capacity=3`，`directed_arcs=10100`
  - 参考值：`objective=41618`
  - 数据特征：`XML100` series，容量下界 `route_lb=34`，总需求 `total_demand=100`。
  - 统计特征：`demand_cv=0`，`distance_cv=0.5568`，`nn_cv=0.8345`，`depot_distance_cv=0.16`

- `cvrplib_XML100_1211_15`
  - 问题描述：CVRPLIB CVRP 实例 `XML100_1211_15`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线，目标是在固定车辆数 `25` 下最小化总路线距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=25`，`capacity=4`，`directed_arcs=10100`
  - 参考值：`objective=16187`
  - 数据特征：`XML100` series，容量下界 `route_lb=25`，总需求 `total_demand=100`。
  - 统计特征：`demand_cv=0`，`distance_cv=0.7103`，`nn_cv=0.8844`，`depot_distance_cv=0.831`

- `cvrplib_XML100_1212_09`
  - 问题描述：CVRPLIB CVRP 实例 `XML100_1212_09`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线，目标是在固定车辆数 `20` 下最小化总路线距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=20`，`capacity=5`，`directed_arcs=10100`
  - 参考值：`objective=20586`
  - 数据特征：`XML100` series，容量下界 `route_lb=20`，总需求 `total_demand=100`。
  - 统计特征：`demand_cv=0`，`distance_cv=0.6868`，`nn_cv=1.8835`，`depot_distance_cv=0.3226`

- `cvrplib_XML100_1213_06`
  - 问题描述：CVRPLIB CVRP 实例 `XML100_1213_06`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线，目标是在固定车辆数 `10` 下最小化总路线距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=10`，`capacity=10`，`directed_arcs=10100`
  - 参考值：`objective=12899`
  - 数据特征：`XML100` series，容量下界 `route_lb=10`，总需求 `total_demand=100`。
  - 统计特征：`demand_cv=0`，`distance_cv=0.6306`，`nn_cv=0.7902`，`depot_distance_cv=0.505`

- `cvrplib_XML100_1215_22`
  - 问题描述：CVRPLIB CVRP 实例 `XML100_1215_22`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线，目标是在固定车辆数 `6` 下最小化总路线距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=6`，`capacity=19`，`directed_arcs=10100`
  - 参考值：`objective=11972`
  - 数据特征：`XML100` series，容量下界 `route_lb=6`，总需求 `total_demand=100`。
  - 统计特征：`demand_cv=0`，`distance_cv=0.6967`，`nn_cv=0.9785`，`depot_distance_cv=0.1118`

- `cvrplib_XML100_1216_04`
  - 问题描述：CVRPLIB CVRP 实例 `XML100_1216_04`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线，目标是在固定车辆数 `3` 下最小化总路线距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=3`，`capacity=38`，`directed_arcs=10100`
  - 参考值：`objective=6068`
  - 数据特征：`XML100` series，容量下界 `route_lb=3`，总需求 `total_demand=100`。
  - 统计特征：`demand_cv=0`，`distance_cv=0.57`，`nn_cv=0.7862`，`depot_distance_cv=0.5845`

- `cvrplib_XML100_1221_07`
  - 问题描述：CVRPLIB CVRP 实例 `XML100_1221_07`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线，目标是在固定车辆数 `21` 下最小化总路线距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=21`，`capacity=27`，`directed_arcs=10100`
  - 参考值：`objective=19773`
  - 数据特征：`XML100` series，容量下界 `route_lb=21`，总需求 `total_demand=563`。
  - 统计特征：`demand_cv=0.5432`，`distance_cv=0.6939`，`nn_cv=1.3118`，`depot_distance_cv=0.5647`

- `cvrplib_XML100_1232_22`
  - 问题描述：CVRPLIB CVRP 实例 `XML100_1232_22`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线，目标是在固定车辆数 `17` 下最小化总路线距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=17`，`capacity=46`，`directed_arcs=10100`
  - 参考值：`objective=18369`
  - 数据特征：`XML100` series，容量下界 `route_lb=16`，总需求 `total_demand=735`。
  - 统计特征：`demand_cv=0.2272`，`distance_cv=0.8775`，`nn_cv=0.9671`，`depot_distance_cv=0.1377`

- `cvrplib_XML100_1241_06`
  - 问题描述：CVRPLIB CVRP 实例 `XML100_1241_06`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线，目标是在固定车辆数 `32` 下最小化总路线距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=32`，`capacity=177`，`directed_arcs=10100`
  - 参考值：`objective=27762`
  - 数据特征：`XML100` series，容量下界 `route_lb=31`，总需求 `total_demand=5412`。
  - 统计特征：`demand_cv=0.5375`，`distance_cv=0.6723`，`nn_cv=0.856`，`depot_distance_cv=0.4388`

- `cvrplib_XML100_1246_16`
  - 问题描述：CVRPLIB CVRP 实例 `XML100_1246_16`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线，目标是在固定车辆数 `3` 下最小化总路线距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=3`，`capacity=2371`，`directed_arcs=10100`
  - 参考值：`objective=5439`
  - 数据特征：`XML100` series，容量下界 `route_lb=3`，总需求 `total_demand=4832`。
  - 统计特征：`demand_cv=0.6551`，`distance_cv=0.7741`，`nn_cv=1.5066`，`depot_distance_cv=0.2093`

- `cvrplib_XML100_1246_25`
  - 问题描述：CVRPLIB CVRP 实例 `XML100_1246_25`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线，目标是在固定车辆数 `4` 下最小化总路线距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=4`，`capacity=1664`，`directed_arcs=10100`
  - 参考值：`objective=5301`
  - 数据特征：`XML100` series，容量下界 `route_lb=4`，总需求 `total_demand=5053`。
  - 统计特征：`demand_cv=0.5871`，`distance_cv=0.7621`，`nn_cv=0.8286`，`depot_distance_cv=0.3569`

- `cvrplib_XML100_1253_05`
  - 问题描述：CVRPLIB CVRP 实例 `XML100_1253_05`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线，目标是在固定车辆数 `12` 下最小化总路线距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=12`，`capacity=631`，`directed_arcs=10100`
  - 参考值：`objective=10310`
  - 数据特征：`XML100` series，容量下界 `route_lb=12`，总需求 `total_demand=7301`。
  - 统计特征：`demand_cv=0.1982`，`distance_cv=0.785`，`nn_cv=1.0318`，`depot_distance_cv=0.9719`

- `cvrplib_XML100_1253_06`
  - 问题描述：CVRPLIB CVRP 实例 `XML100_1253_06`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线，目标是在固定车辆数 `9` 下最小化总路线距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=9`，`capacity=873`，`directed_arcs=10100`
  - 参考值：`objective=16878`
  - 数据特征：`XML100` series，容量下界 `route_lb=9`，总需求 `total_demand=7474`。
  - 统计特征：`demand_cv=0.1869`，`distance_cv=0.7754`，`nn_cv=0.7387`，`depot_distance_cv=0.0855`

- `cvrplib_XML100_1261_02`
  - 问题描述：CVRPLIB CVRP 实例 `XML100_1261_02`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线，目标是在固定车辆数 `33` 下最小化总路线距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=33`，`capacity=183`，`directed_arcs=10100`
  - 参考值：`objective=24376`
  - 数据特征：`XML100` series，容量下界 `route_lb=31`，总需求 `total_demand=5668`。
  - 统计特征：`demand_cv=0.5007`，`distance_cv=0.5825`，`nn_cv=0.9776`，`depot_distance_cv=0.6635`

- `cvrplib_XML100_1272_26`
  - 问题描述：CVRPLIB CVRP 实例 `XML100_1272_26`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线，目标是在固定车辆数 `15` 下最小化总路线距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=15`，`capacity=134`，`directed_arcs=10100`
  - 参考值：`objective=19200`
  - 数据特征：`XML100` series，容量下界 `route_lb=15`，总需求 `total_demand=1933`。
  - 统计特征：`demand_cv=1.4983`，`distance_cv=0.7902`，`nn_cv=1.1113`，`depot_distance_cv=0.4466`

- `cvrplib_XML100_1273_14`
  - 问题描述：CVRPLIB CVRP 实例 `XML100_1273_14`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线，目标是在固定车辆数 `9` 下最小化总路线距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=9`，`capacity=142`，`directed_arcs=10100`
  - 参考值：`objective=17552`
  - 数据特征：`XML100` series，容量下界 `route_lb=9`，总需求 `total_demand=1220`。
  - 统计特征：`demand_cv=1.5677`，`distance_cv=0.6062`，`nn_cv=1.2716`，`depot_distance_cv=0.1213`

- `cvrplib_XML100_1274_15`
  - 问题描述：CVRPLIB CVRP 实例 `XML100_1274_15`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线，目标是在固定车辆数 `7` 下最小化总路线距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=7`，`capacity=179`，`directed_arcs=10100`
  - 参考值：`objective=5827`
  - 数据特征：`XML100` series，容量下界 `route_lb=7`，总需求 `total_demand=1119`。
  - 统计特征：`demand_cv=1.7784`，`distance_cv=0.567`，`nn_cv=0.662`，`depot_distance_cv=0.5089`

- `cvrplib_XML100_2261_21`
  - 问题描述：CVRPLIB CVRP 实例 `XML100_2261_21`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线，目标是在固定车辆数 `21` 下最小化总路线距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=21`，`capacity=226`，`directed_arcs=10100`
  - 参考值：`objective=22453`
  - 数据特征：`XML100` series，容量下界 `route_lb=21`，总需求 `total_demand=4584`。
  - 统计特征：`demand_cv=0.6454`，`distance_cv=0.7674`，`nn_cv=1.3239`，`depot_distance_cv=0.1554`

- `cvrplib_XML100_2376_10`
  - 问题描述：CVRPLIB CVRP 实例 `XML100_2376_10`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线，目标是在固定车辆数 `2` 下最小化总路线距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=2`，`capacity=371`，`directed_arcs=10100`
  - 参考值：`objective=7533`
  - 数据特征：`XML100` series，容量下界 `route_lb=2`，总需求 `total_demand=742`。
  - 统计特征：`demand_cv=1.6432`，`distance_cv=0.5321`，`nn_cv=0.8107`，`depot_distance_cv=0.3484`

- `cvrplib_XML100_3224_11`
  - 问题描述：CVRPLIB CVRP 实例 `XML100_3224_11`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线，目标是在固定车辆数 `7` 下最小化总路线距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=7`，`capacity=73`，`directed_arcs=10100`
  - 参考值：`objective=10464`
  - 数据特征：`XML100` series，容量下界 `route_lb=7`，总需求 `total_demand=509`。
  - 统计特征：`demand_cv=0.5782`，`distance_cv=0.6997`，`nn_cv=0.8728`，`depot_distance_cv=0.4778`

- `cvrplib_XML100_3236_21`
  - 问题描述：CVRPLIB CVRP 实例 `XML100_3236_21`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线，目标是在固定车辆数 `3` 下最小化总路线距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=3`，`capacity=349`，`directed_arcs=10100`
  - 参考值：`objective=6407`
  - 数据特征：`XML100` series，容量下界 `route_lb=3`，总需求 `total_demand=737`。
  - 统计特征：`demand_cv=0.2276`，`distance_cv=0.8358`，`nn_cv=0.7379`，`depot_distance_cv=0.5156`

- `cvrplib_XML100_3275_11`
  - 问题描述：CVRPLIB CVRP 实例 `XML100_3275_11`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线，目标是在固定车辆数 `5` 下最小化总路线距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=5`，`capacity=201`，`directed_arcs=10100`
  - 参考值：`objective=8078`
  - 数据特征：`XML100` series，容量下界 `route_lb=5`，总需求 `total_demand=951`。
  - 统计特征：`demand_cv=1.9093`，`distance_cv=0.8532`，`nn_cv=1.3577`，`depot_distance_cv=0.4106`

- `cvrplib_X-n106-k14`
  - 问题描述：CVRPLIB CVRP 实例 `X-n106-k14`，从一个 depot 出发为 `105` 个客户设计容量受限车辆路线，目标是在固定车辆数 `14` 下最小化总路线距离。
  - 规模：`nodes=106`，`customers=105`，`vehicles=14`，`capacity=600`，`directed_arcs=11130`
  - 参考值：`objective=26362`
  - 数据特征：`X` series，容量下界 `route_lb=14`，总需求 `total_demand=7864`。
  - 统计特征：`demand_cv=0.2078`，`distance_cv=0.6154`，`nn_cv=0.9044`，`depot_distance_cv=0.2529`

- `cvrplib_Tai150c`
  - 问题描述：CVRPLIB CVRP 实例 `Tai150c`，从一个 depot 出发为 `150` 个客户设计容量受限车辆路线，目标是在固定车辆数 `15` 下最小化总路线距离。
  - 规模：`nodes=151`，`customers=150`，`vehicles=15`，`capacity=2021`，`directed_arcs=22650`
  - 参考值：`objective=2358.66`
  - 数据特征：`Tai150c` series，容量下界 `route_lb=14`，总需求 `total_demand=28048`。
  - 统计特征：`demand_cv=1.4456`，`distance_cv=0.6353`，`nn_cv=0.9173`，`depot_distance_cv=0.7545`

- `cvrplib_X-n157-k13`
  - 问题描述：CVRPLIB CVRP 实例 `X-n157-k13`，从一个 depot 出发为 `156` 个客户设计容量受限车辆路线，目标是在固定车辆数 `13` 下最小化总路线距离。
  - 规模：`nodes=157`，`customers=156`，`vehicles=13`，`capacity=12`，`directed_arcs=24492`
  - 参考值：`objective=16876`
  - 数据特征：`X` series，容量下界 `route_lb=13`，总需求 `total_demand=156`。
  - 统计特征：`demand_cv=0`，`distance_cv=0.7165`，`nn_cv=1.0992`，`depot_distance_cv=0.3507`

- `cvrplib_X-n172-k51`
  - 问题描述：CVRPLIB CVRP 实例 `X-n172-k51`，从一个 depot 出发为 `171` 个客户设计容量受限车辆路线，目标是在固定车辆数 `51` 下最小化总路线距离。
  - 规模：`nodes=172`，`customers=171`，`vehicles=51`，`capacity=161`，`directed_arcs=29412`
  - 参考值：`objective=45607`
  - 数据特征：`X` series，容量下界 `route_lb=51`，总需求 `total_demand=8092`。
  - 统计特征：`demand_cv=0.5892`，`distance_cv=0.495`，`nn_cv=0.7732`，`depot_distance_cv=0.4362`


### full

- `cvrplib_Golden_5`
  - 问题描述：CVRPLIB CVRP 实例 `Golden_5`，从一个 depot 出发为 `200` 个客户设计容量受限车辆路线，目标是在固定车辆数 `5` 下最小化总路线距离。
  - 规模：`nodes=201`，`customers=200`，`vehicles=5`，`capacity=900`，`directed_arcs=40200`
  - 参考值：`objective=6460.98`
  - 数据特征：`Golden` series，容量下界 `route_lb=5`，总需求 `total_demand=4000`。
  - 统计特征：`demand_cv=0.5`，`distance_cv=0.4993`，`nn_cv=0.2493`，`depot_distance_cv=0.5222`

- `cvrplib_X-n204-k19`
  - 问题描述：CVRPLIB CVRP 实例 `X-n204-k19`，从一个 depot 出发为 `203` 个客户设计容量受限车辆路线，目标是在固定车辆数 `19` 下最小化总路线距离。
  - 规模：`nodes=204`，`customers=203`，`vehicles=19`，`capacity=836`，`directed_arcs=41412`
  - 参考值：`objective=19565`
  - 数据特征：`X` series，容量下界 `route_lb=19`，总需求 `total_demand=15135`。
  - 统计特征：`demand_cv=0.1936`，`distance_cv=0.537`，`nn_cv=0.6935`，`depot_distance_cv=0.398`

- `cvrplib_X-n219-k73`
  - 问题描述：CVRPLIB CVRP 实例 `X-n219-k73`，从一个 depot 出发为 `218` 个客户设计容量受限车辆路线，目标是在固定车辆数 `73` 下最小化总路线距离。
  - 规模：`nodes=219`，`customers=218`，`vehicles=73`，`capacity=3`，`directed_arcs=47742`
  - 参考值：`objective=117595`
  - 数据特征：`X` series，容量下界 `route_lb=73`，总需求 `total_demand=218`。
  - 统计特征：`demand_cv=0`，`distance_cv=0.4714`，`nn_cv=0.5185`，`depot_distance_cv=0.3809`

- `cvrplib_X-n228-k23`
  - 问题描述：CVRPLIB CVRP 实例 `X-n228-k23`，从一个 depot 出发为 `227` 个客户设计容量受限车辆路线，目标是在固定车辆数 `23` 下最小化总路线距离。
  - 规模：`nodes=228`，`customers=227`，`vehicles=23`，`capacity=154`，`directed_arcs=51756`
  - 参考值：`objective=25742`
  - 数据特征：`X` series，容量下界 `route_lb=23`，总需求 `total_demand=3478`。
  - 统计特征：`demand_cv=1.5685`，`distance_cv=0.5987`，`nn_cv=0.8991`，`depot_distance_cv=0.3433`

- `cvrplib_X-n237-k14`
  - 问题描述：CVRPLIB CVRP 实例 `X-n237-k14`，从一个 depot 出发为 `236` 个客户设计容量受限车辆路线，目标是在固定车辆数 `14` 下最小化总路线距离。
  - 规模：`nodes=237`，`customers=236`，`vehicles=14`，`capacity=18`，`directed_arcs=55932`
  - 参考值：`objective=27042`
  - 数据特征：`X` series，容量下界 `route_lb=14`，总需求 `total_demand=236`。
  - 统计特征：`demand_cv=0`，`distance_cv=0.4721`，`nn_cv=0.5467`，`depot_distance_cv=0.3731`

- `cvrplib_Golden_17`
  - 问题描述：CVRPLIB CVRP 实例 `Golden_17`，从一个 depot 出发为 `240` 个客户设计容量受限车辆路线，目标是在固定车辆数 `22` 下最小化总路线距离。
  - 规模：`nodes=241`，`customers=240`，`vehicles=22`，`capacity=200`，`directed_arcs=57840`
  - 参考值：`objective=707.756`
  - 数据特征：`Golden` series，容量下界 `route_lb=22`，总需求 `total_demand=4320`。
  - 统计特征：`demand_cv=0.6479`，`distance_cv=0.4766`，`nn_cv=0.51`，`depot_distance_cv=0.326`

- `cvrplib_ORTEC-n242-k12`
  - 问题描述：CVRPLIB CVRP 实例 `ORTEC-n242-k12`，从一个 depot 出发为 `241` 个客户设计容量受限车辆路线，目标是在固定车辆数 `12` 下最小化总路线距离。
  - 规模：`nodes=242`，`customers=241`，`vehicles=12`，`capacity=125`，`directed_arcs=58322`
  - 参考值：`objective=123750`
  - 数据特征：`ORTEC` series，容量下界 `route_lb=12`，总需求 `total_demand=1471`。
  - 统计特征：`demand_cv=0.4016`，`distance_cv=0.6785`，`nn_cv=0.8383`，`depot_distance_cv=0.5521`

- `cvrplib_Golden_13`
  - 问题描述：CVRPLIB CVRP 实例 `Golden_13`，从一个 depot 出发为 `252` 个客户设计容量受限车辆路线，目标是在固定车辆数 `26` 下最小化总路线距离。
  - 规模：`nodes=253`，`customers=252`，`vehicles=26`，`capacity=1000`，`directed_arcs=63756`
  - 参考值：`objective=857.189`
  - 数据特征：`Golden` series，容量下界 `route_lb=26`，总需求 `total_demand=25136`。
  - 统计特征：`demand_cv=0.562`，`distance_cv=0.4693`，`nn_cv=0`，`depot_distance_cv=0.3515`

- `cvrplib_X-n280-k17`
  - 问题描述：CVRPLIB CVRP 实例 `X-n280-k17`，从一个 depot 出发为 `279` 个客户设计容量受限车辆路线，目标是在固定车辆数 `17` 下最小化总路线距离。
  - 规模：`nodes=280`，`customers=279`，`vehicles=17`，`capacity=192`，`directed_arcs=78120`
  - 参考值：`objective=33503`
  - 数据特征：`X` series，容量下界 `route_lb=17`，总需求 `total_demand=3233`。
  - 统计特征：`demand_cv=1.7428`，`distance_cv=0.4727`，`nn_cv=0.4531`，`depot_distance_cv=0.3802`

- `cvrplib_X-n284-k15`
  - 问题描述：CVRPLIB CVRP 实例 `X-n284-k15`，从一个 depot 出发为 `283` 个客户设计容量受限车辆路线，目标是在固定车辆数 `15` 下最小化总路线距离。
  - 规模：`nodes=284`，`customers=283`，`vehicles=15`，`capacity=109`，`directed_arcs=80372`
  - 参考值：`objective=20215`
  - 数据特征：`X` series，容量下界 `route_lb=15`，总需求 `total_demand=1527`。
  - 统计特征：`demand_cv=0.5306`，`distance_cv=0.5337`，`nn_cv=1.3753`，`depot_distance_cv=0.3302`

- `cvrplib_X-n313-k71`
  - 问题描述：CVRPLIB CVRP 实例 `X-n313-k71`，从一个 depot 出发为 `312` 个客户设计容量受限车辆路线，目标是在固定车辆数 `71` 下最小化总路线距离。
  - 规模：`nodes=313`，`customers=312`，`vehicles=71`，`capacity=248`，`directed_arcs=97656`
  - 参考值：`objective=94043`
  - 数据特征：`X` series，容量下界 `route_lb=71`，总需求 `total_demand=17545`。
  - 统计特征：`demand_cv=0.4841`，`distance_cv=0.5264`，`nn_cv=0.6847`，`depot_distance_cv=0.4058`

- `cvrplib_X-n317-k53`
  - 问题描述：CVRPLIB CVRP 实例 `X-n317-k53`，从一个 depot 出发为 `316` 个客户设计容量受限车辆路线，目标是在固定车辆数 `53` 下最小化总路线距离。
  - 规模：`nodes=317`，`customers=316`，`vehicles=53`，`capacity=6`，`directed_arcs=100172`
  - 参考值：`objective=78355`
  - 数据特征：`X` series，容量下界 `route_lb=53`，总需求 `total_demand=316`。
  - 统计特征：`demand_cv=0`，`distance_cv=0.6219`，`nn_cv=1.1342`，`depot_distance_cv=0.5246`

- `cvrplib_Tai385`
  - 问题描述：CVRPLIB CVRP 实例 `Tai385`，从一个 depot 出发为 `385` 个客户设计容量受限车辆路线，目标是在固定车辆数 `47` 下最小化总路线距离。
  - 规模：`nodes=386`，`customers=385`，`vehicles=47`，`capacity=65`，`directed_arcs=148610`
  - 参考值：`objective=24366.4134`
  - 数据特征：`Tai385` series，容量下界 `route_lb=46`，总需求 `total_demand=2983`。
  - 统计特征：`demand_cv=1.4173`，`distance_cv=0.5736`，`nn_cv=0.5581`，`depot_distance_cv=0.5068`

- `cvrplib_Loggi-n401-k23`
  - 问题描述：CVRPLIB CVRP 实例 `Loggi-n401-k23`，从一个 depot 出发为 `400` 个客户设计容量受限车辆路线，目标是在固定车辆数 `23` 下最小化总路线距离。
  - 规模：`nodes=401`，`customers=400`，`vehicles=23`，`capacity=100`，`directed_arcs=160400`
  - 参考值：`objective=336903`
  - 数据特征：`Loggi` series，容量下界 `route_lb=23`，总需求 `total_demand=2237`。
  - 统计特征：`demand_cv=0.4996`，`distance_cv=0.9332`，`nn_cv=1.7943`，`depot_distance_cv=0.268`

- `cvrplib_ORTEC-n455-k41`
  - 问题描述：CVRPLIB CVRP 实例 `ORTEC-n455-k41`，从一个 depot 出发为 `454` 个客户设计容量受限车辆路线，目标是在固定车辆数 `41` 下最小化总路线距离。
  - 规模：`nodes=455`，`customers=454`，`vehicles=41`，`capacity=70`，`directed_arcs=206570`
  - 参考值：`objective=292485`
  - 数据特征：`ORTEC` series，容量下界 `route_lb=41`，总需求 `total_demand=2860`。
  - 统计特征：`demand_cv=0.3696`，`distance_cv=0.8495`，`nn_cv=0.931`，`depot_distance_cv=0.8368`


### pressure

- `cvrplib_Loggi-n501-k24`
  - 问题描述：CVRPLIB CVRP 实例 `Loggi-n501-k24`，从一个 depot 出发为 `500` 个客户设计容量受限车辆路线，目标是在固定车辆数 `24` 下最小化总路线距离。
  - 规模：`nodes=501`，`customers=500`，`vehicles=24`，`capacity=120`，`directed_arcs=250500`
  - 参考值：`objective=177078`
  - 数据特征：`Loggi` series，容量下界 `route_lb=24`，总需求 `total_demand=2774`。
  - 统计特征：`demand_cv=0.52`，`distance_cv=0.6385`，`nn_cv=1.4831`，`depot_distance_cv=0.6867`

- `cvrplib_X-n502-k39`
  - 问题描述：CVRPLIB CVRP 实例 `X-n502-k39`，从一个 depot 出发为 `501` 个客户设计容量受限车辆路线，目标是在固定车辆数 `39` 下最小化总路线距离。
  - 规模：`nodes=502`，`customers=501`，`vehicles=39`，`capacity=13`，`directed_arcs=251502`
  - 参考值：`objective=69226`
  - 数据特征：`X` series，容量下界 `route_lb=39`，总需求 `total_demand=501`。
  - 统计特征：`demand_cv=0`，`distance_cv=0.7269`，`nn_cv=1.4012`，`depot_distance_cv=0.1815`

- `cvrplib_ORTEC-n510-k23`
  - 问题描述：CVRPLIB CVRP 实例 `ORTEC-n510-k23`，从一个 depot 出发为 `509` 个客户设计容量受限车辆路线，目标是在固定车辆数 `23` 下最小化总路线距离。
  - 规模：`nodes=510`，`customers=509`，`vehicles=23`，`capacity=145`，`directed_arcs=259590`
  - 参考值：`objective=184529`
  - 数据特征：`ORTEC` series，容量下界 `route_lb=23`，总需求 `total_demand=3232`。
  - 统计特征：`demand_cv=0.4089`，`distance_cv=0.6295`，`nn_cv=0.6849`，`depot_distance_cv=0.3011`

- `cvrplib_X-n524-k153`
  - 问题描述：CVRPLIB CVRP 实例 `X-n524-k153`，从一个 depot 出发为 `523` 个客户设计容量受限车辆路线，目标是在固定车辆数 `153` 下最小化总路线距离。
  - 规模：`nodes=524`，`customers=523`，`vehicles=153`，`capacity=125`，`directed_arcs=274052`
  - 参考值：`objective=154593`
  - 数据特征：`X` series，容量下界 `route_lb=137`，总需求 `total_demand=17067`。
  - 统计特征：`demand_cv=1.0707`，`distance_cv=0.4763`，`nn_cv=0.4992`，`depot_distance_cv=0.4572`

- `cvrplib_X-n536-k96`
  - 问题描述：CVRPLIB CVRP 实例 `X-n536-k96`，从一个 depot 出发为 `535` 个客户设计容量受限车辆路线，目标是在固定车辆数 `96` 下最小化总路线距离。
  - 规模：`nodes=536`，`customers=535`，`vehicles=96`，`capacity=371`，`directed_arcs=286760`
  - 参考值：`objective=94846`
  - 数据特征：`X` series，容量下界 `route_lb=96`，总需求 `total_demand=35423`。
  - 统计特征：`demand_cv=0.3582`，`distance_cv=0.6259`，`nn_cv=1.0864`，`depot_distance_cv=0.2853`

- `cvrplib_X-n548-k50`
  - 问题描述：CVRPLIB CVRP 实例 `X-n548-k50`，从一个 depot 出发为 `547` 个客户设计容量受限车辆路线，目标是在固定车辆数 `50` 下最小化总路线距离。
  - 规模：`nodes=548`，`customers=547`，`vehicles=50`，`capacity=11`，`directed_arcs=299756`
  - 参考值：`objective=86700`
  - 数据特征：`X` series，容量下界 `route_lb=50`，总需求 `total_demand=547`。
  - 统计特征：`demand_cv=0`，`distance_cv=0.4737`，`nn_cv=0.5149`，`depot_distance_cv=0.3653`

- `cvrplib_Li_21`
  - 问题描述：CVRPLIB CVRP 实例 `Li_21`，从一个 depot 出发为 `560` 个客户设计容量受限车辆路线，目标是在固定车辆数 `10` 下最小化总路线距离。
  - 规模：`nodes=561`，`customers=560`，`vehicles=10`，`capacity=1200`，`directed_arcs=314160`
  - 参考值：`objective=16212.8255`
  - 数据特征：`Li` series，容量下界 `route_lb=10`，总需求 `total_demand=11200`。
  - 统计特征：`demand_cv=0.5`，`distance_cv=0.5064`，`nn_cv=0.3518`，`depot_distance_cv=0.5375`

- `cvrplib_X-n573-k30`
  - 问题描述：CVRPLIB CVRP 实例 `X-n573-k30`，从一个 depot 出发为 `572` 个客户设计容量受限车辆路线，目标是在固定车辆数 `30` 下最小化总路线距离。
  - 规模：`nodes=573`，`customers=572`，`vehicles=30`，`capacity=210`，`directed_arcs=327756`
  - 参考值：`objective=50673`
  - 数据特征：`X` series，容量下界 `route_lb=30`，总需求 `total_demand=6172`。
  - 统计特征：`demand_cv=1.8254`，`distance_cv=0.5614`，`nn_cv=1.4394`，`depot_distance_cv=0.1563`

- `cvrplib_Loggi-n601-k19`
  - 问题描述：CVRPLIB CVRP 实例 `Loggi-n601-k19`，从一个 depot 出发为 `600` 个客户设计容量受限车辆路线，目标是在固定车辆数 `19` 下最小化总路线距离。
  - 规模：`nodes=601`，`customers=600`，`vehicles=19`，`capacity=180`，`directed_arcs=360600`
  - 参考值：`objective=113155`
  - 数据特征：`Loggi` series，容量下界 `route_lb=19`，总需求 `total_demand=3352`。
  - 统计特征：`demand_cv=0.4977`，`distance_cv=0.923`，`nn_cv=2.4604`，`depot_distance_cv=0.971`

- `cvrplib_Loggi-n601-k42`
  - 问题描述：CVRPLIB CVRP 实例 `Loggi-n601-k42`，从一个 depot 出发为 `600` 个客户设计容量受限车辆路线，目标是在固定车辆数 `42` 下最小化总路线距离。
  - 规模：`nodes=601`，`customers=600`，`vehicles=42`，`capacity=80`，`directed_arcs=360600`
  - 参考值：`objective=347046`
  - 数据特征：`Loggi` series，容量下界 `route_lb=42`，总需求 `total_demand=3289`。
  - 统计特征：`demand_cv=0.5193`，`distance_cv=0.5516`，`nn_cv=1.1126`，`depot_distance_cv=0.497`

- `cvrplib_X-n613-k62`
  - 问题描述：CVRPLIB CVRP 实例 `X-n613-k62`，从一个 depot 出发为 `612` 个客户设计容量受限车辆路线，目标是在固定车辆数 `62` 下最小化总路线距离。
  - 规模：`nodes=613`，`customers=612`，`vehicles=62`，`capacity=523`，`directed_arcs=375156`
  - 参考值：`objective=59535`
  - 数据特征：`X` series，容量下界 `route_lb=62`，总需求 `total_demand=32002`。
  - 统计特征：`demand_cv=0.5417`，`distance_cv=0.4744`，`nn_cv=0.5187`，`depot_distance_cv=0.3543`

- `cvrplib_X-n655-k131`
  - 问题描述：CVRPLIB CVRP 实例 `X-n655-k131`，从一个 depot 出发为 `654` 个客户设计容量受限车辆路线，目标是在固定车辆数 `131` 下最小化总路线距离。
  - 规模：`nodes=655`，`customers=654`，`vehicles=131`，`capacity=5`，`directed_arcs=428370`
  - 参考值：`objective=106780`
  - 数据特征：`X` series，容量下界 `route_lb=131`，总需求 `total_demand=654`。
  - 统计特征：`demand_cv=0`，`distance_cv=0.6288`，`nn_cv=0.9764`，`depot_distance_cv=0.2522`

- `cvrplib_ORTEC-n701-k64`
  - 问题描述：CVRPLIB CVRP 实例 `ORTEC-n701-k64`，从一个 depot 出发为 `700` 个客户设计容量受限车辆路线，目标是在固定车辆数 `64` 下最小化总路线距离。
  - 规模：`nodes=701`，`customers=700`，`vehicles=64`，`capacity=80`，`directed_arcs=490700`
  - 参考值：`objective=445541`
  - 数据特征：`ORTEC` series，容量下界 `route_lb=64`，总需求 `total_demand=5049`。
  - 统计特征：`demand_cv=0.4927`，`distance_cv=0.5781`，`nn_cv=1.8521`，`depot_distance_cv=0.4443`

- `cvrplib_X-n716-k35`
  - 问题描述：CVRPLIB CVRP 实例 `X-n716-k35`，从一个 depot 出发为 `715` 个客户设计容量受限车辆路线，目标是在固定车辆数 `35` 下最小化总路线距离。
  - 规模：`nodes=716`，`customers=715`，`vehicles=35`，`capacity=1007`，`directed_arcs=511940`
  - 参考值：`objective=43373`
  - 数据特征：`X` series，容量下界 `route_lb=35`，总需求 `total_demand=34266`。
  - 统计特征：`demand_cv=0.5939`，`distance_cv=0.6461`，`nn_cv=1.05`，`depot_distance_cv=0.4848`

- `cvrplib_X-n916-k207`
  - 问题描述：CVRPLIB CVRP 实例 `X-n916-k207`，从一个 depot 出发为 `915` 个客户设计容量受限车辆路线，目标是在固定车辆数 `207` 下最小化总路线距离。
  - 规模：`nodes=916`，`customers=915`，`vehicles=207`，`capacity=33`，`directed_arcs=838140`
  - 参考值：`objective=329179`
  - 数据特征：`X` series，容量下界 `route_lb=207`，总需求 `total_demand=6816`。
  - 统计特征：`demand_cv=0.2338`，`distance_cv=0.5061`，`nn_cv=0.6495`，`depot_distance_cv=0.3341`

- `cvrplib_XL-n1094-k157`
  - 问题描述：CVRPLIB CVRP 实例 `XL-n1094-k157`，从一个 depot 出发为 `1093` 个客户设计容量受限车辆路线，目标是在固定车辆数 `157` 下最小化总路线距离。
  - 规模：`nodes=1094`，`customers=1093`，`vehicles=157`，`capacity=7`，`directed_arcs=1195742`
  - 参考值：`objective=112431`
  - 数据特征：`XL` series，容量下界 `route_lb=157`，总需求 `total_demand=1093`。
  - 统计特征：`demand_cv=0`，`distance_cv=0.5717`，`nn_cv=1.0575`，`depot_distance_cv=0.4836`


## 问题定义

每个 case 都是在给定一个 depot、若干客户、客户需求、车辆容量、固定车辆数和节点间距离度量的前提下，寻找若干条车辆路线。每条路线从 depot 出发并回到 depot，每个客户恰好被访问一次，任一路线上的客户需求总和不能超过车辆容量，最终目标是最小化所有路线的总行驶距离。

CVRP 是 VRP 家族中的容量约束基础变体。与 TSP 相比，CVRP 不只需要决定客户访问顺序，还需要决定客户如何分配到多辆车或多条路线中，因此同等节点规模下通常具有更高的组合复杂度。
