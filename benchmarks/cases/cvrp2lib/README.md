# CVRP2LIB 数据来源说明

CVRP2LIB 目录保存从 CVRPLIB XML100 生成族中筛选出的特殊 CVRP_XML benchmark case。该数据集与 `cvrplib/cvrp` 分开维护：`cvrplib/cvrp` 按固定车辆数最小化距离建模，而 `cvrp2lib/cvrp_xml` 保留 XML100 原始不固定车辆数的输入口径，用于后续测试 OptAgent 在车辆数和路线距离共同变化场景下的表现。

数据集来源：

- CVRPLIB 主页：https://vrp.atd-lab.inf.puc-rio.br/index.php/en/
- CVRPLIB XML100 数据说明与实例来源：https://vrp.atd-lab.inf.puc-rio.br/index.php/en/
- 本地完整 XML100 数据缓存：`benchmarks/cases/cvrp2lib/cvrp_xml/raw/XML/`
- 正式筛选 case：`benchmarks/cases/cvrp2lib/cvrp_xml/raw/` 根层的 `.vrp`、`.sol` 和 `.json` 文件

筛选后的正式候选 case 会复制到 `cvrp_xml/raw/` 根层，保证 `--no-download` 时可以直接读取。`.vrp` 文件保留 CVRPLIB XML100 原始格式，`.sol` 文件保留官方参考解，`.json` 文件是 benchmark loader 后续使用的结构化格式。

当前 `cvrp2lib/cvrp_xml` 统一按 CVRP_XML 口径处理：输入侧 `size.vehicles` 保持 `null`，表示原始实例不提供固定车辆数；`reference.vehicles` 记录官方参考解实际使用的路线数，`reference.objective` 记录该参考解的总距离。与 `cvrplib/cvrp` 不同，本数据集不把参考解路线数写回输入车辆数。

## JSON 数据格式说明

当前结构化文件为 `cvrp_xml/raw/<instance>.json`。每个 JSON 文件包含：

- `name`：XML100 实例名。
- `problem_type`：问题类型，当前为 `CVRP_XML`。
- `source` 和 `series`：数据来源和实例系列，当前分别为 `CVRP2LIB` 和 `XML100`。
- `metadata`：原始注释、距离类型和原始 `.vrp` 文件名。
- `size`：规模信息，包括 `nodes`、`customers`、`vehicles`、`capacity`、`directed_arcs`；其中 `vehicles` 保持 `null`。
- `depot`：仓库节点 id，保留原始 CVRPLIB 节点编号。
- `nodes`：节点列表，每个节点包含 `id`、`x`、`y`、`demand`、`is_depot`。
- `tier`：当前 benchmark 分层，当前选中 case 均为 `calibration`。
- `reference`：当前正式筛选 case 均包含 `.sol` 对应的官方参考解，字段包含 optimal `objective`、路线、路线数、车辆数、状态和来源文件。

注意：`.sol` 文件中的路线使用 CVRPLIB 解文件的客户编号口径，路线中省略 depot；`.json` 中的 `nodes[].id` 保留 `.vrp` 原始节点编号。后续 loader 如需校验参考解，应显式处理这两个编号口径。

## 数据筛选依据

本轮处于算例筛选阶段，候选空间为 XML100 完整数据集。所有实例规模均为 `nodes=101`、`customers=100`，因此筛选重点不再是节点规模，而是容量、需求结构、空间结构和 XML100 名称编码代表的生成机制差异。

相似度特征包含：容量、总需求、容量路线下界、需求均值、需求变异系数、全局距离变异系数、最近邻距离变异系数、仓库距离变异系数、坐标长宽比、空间密度，以及 XML100 名称中的 `depot_type`、`customer_distribution`、`demand_distribution`、`route_size`。对容量、总需求、容量路线下界、需求均值和空间密度取 `log1p` 后，基于完整 XML100 数据集做 z-score 标准化，再用加权欧氏距离比较。

筛选过程先保留原始分组 medoid 和远离已有集合的代表样本，再逐步按距离阈值补充差异样本。最终选中 55 个 calibration 算例，并排除与已选集合过近的高相似样本。

## 建模说明

## 相关 case

### calibration

- `cvrp2lib_XML100_1111_24`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_1111_24`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `25` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=4`，`directed_arcs=10100`
  - 参考值：`objective=36733`，`vehicles=25`
  - 数据特征：`XML100` series，容量下界 `route_lb=25`，总需求 `total_demand=100`。
  - 统计特征：`demand_cv=0`，`distance_cv=0.4741`，`nn_cv=0.5257`，`depot_distance_cv=0.451`

- `cvrp2lib_XML100_1124_08`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_1124_08`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `8` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=81`，`directed_arcs=10100`
  - 参考值：`objective=11172`，`vehicles=8`
  - 数据特征：`XML100` series，容量下界 `route_lb=8`，总需求 `total_demand=595`。
  - 统计特征：`demand_cv=0.5133`，`distance_cv=0.4782`，`nn_cv=0.5321`，`depot_distance_cv=0.4463`

- `cvrp2lib_XML100_1141_10`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_1141_10`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `26` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=196`，`directed_arcs=10100`
  - 参考值：`objective=36861`，`vehicles=26`
  - 数据特征：`XML100` series，容量下界 `route_lb=26`，总需求 `total_demand=5003`。
  - 统计特征：`demand_cv=0.6016`，`distance_cv=0.4708`，`nn_cv=0.5517`，`depot_distance_cv=0.4553`

- `cvrp2lib_XML100_1146_17`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_1146_17`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `3` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=1839`，`directed_arcs=10100`
  - 参考值：`objective=8894`，`vehicles=3`
  - 数据特征：`XML100` series，容量下界 `route_lb=3`，总需求 `total_demand=4992`。
  - 统计特征：`demand_cv=0.5812`，`distance_cv=0.4657`，`nn_cv=0.5584`，`depot_distance_cv=0.4489`

- `cvrp2lib_XML100_1175_09`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_1175_09`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `5` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=190`，`directed_arcs=10100`
  - 参考值：`objective=11247`，`vehicles=5`
  - 数据特征：`XML100` series，容量下界 `route_lb=5`，总需求 `total_demand=941`。
  - 统计特征：`demand_cv=1.6734`，`distance_cv=0.4714`，`nn_cv=0.5151`，`depot_distance_cv=0.4475`

- `cvrp2lib_XML100_1211_07`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_1211_07`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `34` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=3`，`directed_arcs=10100`
  - 参考值：`objective=42832`，`vehicles=34`
  - 数据特征：`XML100` series，容量下界 `route_lb=34`，总需求 `total_demand=100`。
  - 统计特征：`demand_cv=0`，`distance_cv=0.5517`，`nn_cv=0.8254`，`depot_distance_cv=0.355`

- `cvrp2lib_XML100_1211_15`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_1211_15`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `25` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=4`，`directed_arcs=10100`
  - 参考值：`objective=16187`，`vehicles=25`
  - 数据特征：`XML100` series，容量下界 `route_lb=25`，总需求 `total_demand=100`。
  - 统计特征：`demand_cv=0`，`distance_cv=0.7138`，`nn_cv=0.8932`，`depot_distance_cv=0.8312`

- `cvrp2lib_XML100_1212_09`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_1212_09`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `20` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=5`，`directed_arcs=10100`
  - 参考值：`objective=20586`，`vehicles=20`
  - 数据特征：`XML100` series，容量下界 `route_lb=20`，总需求 `total_demand=100`。
  - 统计特征：`demand_cv=0`，`distance_cv=0.68`，`nn_cv=1.8878`，`depot_distance_cv=0.3225`

- `cvrp2lib_XML100_1213_13`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_1213_13`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `12` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=9`，`directed_arcs=10100`
  - 参考值：`objective=14176`，`vehicles=12`
  - 数据特征：`XML100` series，容量下界 `route_lb=12`，总需求 `total_demand=100`。
  - 统计特征：`demand_cv=0`，`distance_cv=0.7143`，`nn_cv=1.4352`，`depot_distance_cv=0.1398`

- `cvrp2lib_XML100_1214_16`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_1214_16`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `8` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=13`，`directed_arcs=10100`
  - 参考值：`objective=8375`，`vehicles=8`
  - 数据特征：`XML100` series，容量下界 `route_lb=8`，总需求 `total_demand=100`。
  - 统计特征：`demand_cv=0`，`distance_cv=0.6064`，`nn_cv=0.792`，`depot_distance_cv=0.3318`

- `cvrp2lib_XML100_1216_12`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_1216_12`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `3` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=49`，`directed_arcs=10100`
  - 参考值：`objective=5453`，`vehicles=3`
  - 数据特征：`XML100` series，容量下界 `route_lb=3`，总需求 `total_demand=100`。
  - 统计特征：`demand_cv=0`，`distance_cv=0.5889`，`nn_cv=0.8139`，`depot_distance_cv=0.5077`

- `cvrp2lib_XML100_1216_16`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_1216_16`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `3` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=35`，`directed_arcs=10100`
  - 参考值：`objective=5115`，`vehicles=3`
  - 数据特征：`XML100` series，容量下界 `route_lb=3`，总需求 `total_demand=100`。
  - 统计特征：`demand_cv=0`，`distance_cv=0.6857`，`nn_cv=0.8449`，`depot_distance_cv=0.3222`

- `cvrp2lib_XML100_1221_19`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_1221_19`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `26` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=23`，`directed_arcs=10100`
  - 参考值：`objective=26126`，`vehicles=26`
  - 数据特征：`XML100` series，容量下界 `route_lb=26`，总需求 `total_demand=594`。
  - 统计特征：`demand_cv=0.4778`，`distance_cv=0.6377`，`nn_cv=0.777`，`depot_distance_cv=0.4043`

- `cvrp2lib_XML100_1226_04`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_1226_04`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `3` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=220`，`directed_arcs=10100`
  - 参考值：`objective=7173`，`vehicles=3`
  - 数据特征：`XML100` series，容量下界 `route_lb=3`，总需求 `total_demand=530`。
  - 统计特征：`demand_cv=0.5732`，`distance_cv=0.5537`，`nn_cv=0.829`，`depot_distance_cv=0.3704`

- `cvrp2lib_XML100_1233_17`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_1233_17`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `10` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=76`，`directed_arcs=10100`
  - 参考值：`objective=9283`，`vehicles=10`
  - 数据特征：`XML100` series，容量下界 `route_lb=10`，总需求 `total_demand=744`。
  - 统计特征：`demand_cv=0.217`，`distance_cv=0.5771`，`nn_cv=0.9774`，`depot_distance_cv=0.3497`

- `cvrp2lib_XML100_1234_18`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_1234_18`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `8` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=101`，`directed_arcs=10100`
  - 参考值：`objective=13159`，`vehicles=8`
  - 数据特征：`XML100` series，容量下界 `route_lb=8`，总需求 `total_demand=751`。
  - 统计特征：`demand_cv=0.2084`，`distance_cv=0.8287`，`nn_cv=0.9152`，`depot_distance_cv=0.0888`

- `cvrp2lib_XML100_1234_27`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_1234_27`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `7` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=112`，`directed_arcs=10100`
  - 参考值：`objective=3774`，`vehicles=7`
  - 数据特征：`XML100` series，容量下界 `route_lb=7`，总需求 `total_demand=737`。
  - 统计特征：`demand_cv=0.2235`，`distance_cv=0.5893`，`nn_cv=1.0689`，`depot_distance_cv=0.4855`

- `cvrp2lib_XML100_1241_11`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_1241_11`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `29` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=184`，`directed_arcs=10100`
  - 参考值：`objective=26327`，`vehicles=29`
  - 数据特征：`XML100` series，容量下界 `route_lb=27`，总需求 `total_demand=4952`。
  - 统计特征：`demand_cv=0.542`，`distance_cv=0.5921`，`nn_cv=0.8352`，`depot_distance_cv=0.4918`

- `cvrp2lib_XML100_1253_02`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_1253_02`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `13` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=644`，`directed_arcs=10100`
  - 参考值：`objective=13372`，`vehicles=13`
  - 数据特征：`XML100` series，容量下界 `route_lb=12`，总需求 `total_demand=7727`。
  - 统计特征：`demand_cv=0.1985`，`distance_cv=0.7173`，`nn_cv=1.0676`，`depot_distance_cv=0.7971`

- `cvrp2lib_XML100_1253_05`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_1253_05`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `12` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=631`，`directed_arcs=10100`
  - 参考值：`objective=10310`，`vehicles=12`
  - 数据特征：`XML100` series，容量下界 `route_lb=12`，总需求 `total_demand=7301`。
  - 统计特征：`demand_cv=0.1982`，`distance_cv=0.7886`，`nn_cv=1.0402`，`depot_distance_cv=0.972`

- `cvrp2lib_XML100_1253_06`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_1253_06`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `9` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=873`，`directed_arcs=10100`
  - 参考值：`objective=16878`，`vehicles=9`
  - 数据特征：`XML100` series，容量下界 `route_lb=9`，总需求 `total_demand=7474`。
  - 统计特征：`demand_cv=0.1869`，`distance_cv=0.765`，`nn_cv=0.7393`，`depot_distance_cv=0.0855`

- `cvrp2lib_XML100_1253_08`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_1253_08`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `10` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=806`，`directed_arcs=10100`
  - 参考值：`objective=12317`，`vehicles=10`
  - 数据特征：`XML100` series，容量下界 `route_lb=10`，总需求 `total_demand=7309`。
  - 统计特征：`demand_cv=0.2022`，`distance_cv=0.605`，`nn_cv=0.6067`，`depot_distance_cv=0.2865`

- `cvrp2lib_XML100_1266_07`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_1266_07`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `3` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=2503`，`directed_arcs=10100`
  - 参考值：`objective=6182`，`vehicles=3`
  - 数据特征：`XML100` series，容量下界 `route_lb=3`，总需求 `total_demand=5804`。
  - 统计特征：`demand_cv=0.4749`，`distance_cv=0.5881`，`nn_cv=0.8087`，`depot_distance_cv=0.3016`

- `cvrp2lib_XML100_1271_21`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_1271_21`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `29` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=124`，`directed_arcs=10100`
  - 参考值：`objective=25309`，`vehicles=29`
  - 数据特征：`XML100` series，容量下界 `route_lb=25`，总需求 `total_demand=2986`。
  - 统计特征：`demand_cv=1.1398`，`distance_cv=0.5676`，`nn_cv=0.9388`，`depot_distance_cv=0.3216`

- `cvrp2lib_XML100_1275_26`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_1275_26`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `6` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=188`，`directed_arcs=10100`
  - 参考值：`objective=7463`，`vehicles=6`
  - 数据特征：`XML100` series，容量下界 `route_lb=6`，总需求 `total_demand=979`。
  - 统计特征：`demand_cv=1.8057`，`distance_cv=0.5839`，`nn_cv=0.8676`，`depot_distance_cv=0.3185`

- `cvrp2lib_XML100_1276_11`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_1276_11`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `4` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=248`，`directed_arcs=10100`
  - 参考值：`objective=4455`，`vehicles=4`
  - 数据特征：`XML100` series，容量下界 `route_lb=4`，总需求 `total_demand=829`。
  - 统计特征：`demand_cv=1.7766`，`distance_cv=0.6277`，`nn_cv=1.0147`，`depot_distance_cv=0.4742`

- `cvrp2lib_XML100_1276_13`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_1276_13`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `3` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=297`，`directed_arcs=10100`
  - 参考值：`objective=6718`，`vehicles=3`
  - 数据特征：`XML100` series，容量下界 `route_lb=3`，总需求 `total_demand=657`。
  - 统计特征：`demand_cv=1.2568`，`distance_cv=0.848`，`nn_cv=1.3178`，`depot_distance_cv=0.0912`

- `cvrp2lib_XML100_1321_06`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_1321_06`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `26` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=21`，`directed_arcs=10100`
  - 参考值：`objective=28192`，`vehicles=26`
  - 数据特征：`XML100` series，容量下界 `route_lb=26`，总需求 `total_demand=534`。
  - 统计特征：`demand_cv=0.5252`，`distance_cv=0.5054`，`nn_cv=0.6964`，`depot_distance_cv=0.4373`

- `cvrp2lib_XML100_1353_10`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_1353_10`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `10` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=770`，`directed_arcs=10100`
  - 参考值：`objective=14047`，`vehicles=10`
  - 数据特征：`XML100` series，容量下界 `route_lb=10`，总需求 `total_demand=7391`。
  - 统计特征：`demand_cv=0.1963`，`distance_cv=0.5332`，`nn_cv=0.7222`，`depot_distance_cv=0.4017`

- `cvrp2lib_XML100_1371_22`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_1371_22`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `22` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=121`，`directed_arcs=10100`
  - 参考值：`objective=29141`，`vehicles=22`
  - 数据特征：`XML100` series，容量下界 `route_lb=22`，总需求 `total_demand=2548`。
  - 统计特征：`demand_cv=1.2085`，`distance_cv=0.491`，`nn_cv=0.6704`，`depot_distance_cv=0.4485`

- `cvrp2lib_XML100_1374_06`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_1374_06`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `8` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=169`，`directed_arcs=10100`
  - 参考值：`objective=10704`，`vehicles=8`
  - 数据特征：`XML100` series，容量下界 `route_lb=8`，总需求 `total_demand=1254`。
  - 统计特征：`demand_cv=1.7076`，`distance_cv=0.5328`，`nn_cv=0.729`，`depot_distance_cv=0.453`

- `cvrp2lib_XML100_2251_15`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_2251_15`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `27` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=292`，`directed_arcs=10100`
  - 参考值：`objective=25519`，`vehicles=27`
  - 数据特征：`XML100` series，容量下界 `route_lb=27`，总需求 `total_demand=7603`。
  - 统计特征：`demand_cv=0.1881`，`distance_cv=0.5644`，`nn_cv=0.7471`，`depot_distance_cv=0.2561`

- `cvrp2lib_XML100_2261_21`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_2261_21`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `21` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=226`，`directed_arcs=10100`
  - 参考值：`objective=22453`，`vehicles=21`
  - 数据特征：`XML100` series，容量下界 `route_lb=21`，总需求 `total_demand=4584`。
  - 统计特征：`demand_cv=0.6454`，`distance_cv=0.7585`，`nn_cv=1.3252`，`depot_distance_cv=0.1555`

- `cvrp2lib_XML100_2266_13`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_2266_13`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `3` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=2765`，`directed_arcs=10100`
  - 参考值：`objective=4832`，`vehicles=3`
  - 数据特征：`XML100` series，容量下界 `route_lb=3`，总需求 `total_demand=7065`。
  - 统计特征：`demand_cv=0.2717`，`distance_cv=0.5834`，`nn_cv=0.8319`，`depot_distance_cv=0.2351`

- `cvrp2lib_XML100_2272_26`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_2272_26`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `14` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=133`，`directed_arcs=10100`
  - 参考值：`objective=14058`，`vehicles=14`
  - 数据特征：`XML100` series，容量下界 `route_lb=14`，总需求 `total_demand=1808`。
  - 统计特征：`demand_cv=1.4462`，`distance_cv=0.6126`，`nn_cv=0.8736`，`depot_distance_cv=0.3921`

- `cvrp2lib_XML100_2324_17`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_2324_17`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `8` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=74`，`directed_arcs=10100`
  - 参考值：`objective=10522`，`vehicles=8`
  - 数据特征：`XML100` series，容量下界 `route_lb=8`，总需求 `total_demand=537`。
  - 统计特征：`demand_cv=0.581`，`distance_cv=0.531`，`nn_cv=0.7422`，`depot_distance_cv=0.3384`

- `cvrp2lib_XML100_3114_25`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_3114_25`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `8` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=13`，`directed_arcs=10100`
  - 参考值：`objective=16179`，`vehicles=8`
  - 数据特征：`XML100` series，容量下界 `route_lb=8`，总需求 `total_demand=100`。
  - 统计特征：`demand_cv=0`，`distance_cv=0.4765`，`nn_cv=0.5525`，`depot_distance_cv=0.375`

- `cvrp2lib_XML100_3121_04`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_3121_04`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `24` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=23`，`directed_arcs=10100`
  - 参考值：`objective=40007`，`vehicles=24`
  - 数据特征：`XML100` series，容量下界 `route_lb=24`，总需求 `total_demand=533`。
  - 统计特征：`demand_cv=0.5483`，`distance_cv=0.479`，`nn_cv=0.5357`，`depot_distance_cv=0.373`

- `cvrp2lib_XML100_3153_01`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_3153_01`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `11` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=684`，`directed_arcs=10100`
  - 参考值：`objective=21516`，`vehicles=11`
  - 数据特征：`XML100` series，容量下界 `route_lb=11`，总需求 `total_demand=7457`。
  - 统计特征：`demand_cv=0.1825`，`distance_cv=0.471`，`nn_cv=0.5301`，`depot_distance_cv=0.3754`

- `cvrp2lib_XML100_3172_25`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_3172_25`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `17` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=124`，`directed_arcs=10100`
  - 参考值：`objective=31657`，`vehicles=17`
  - 数据特征：`XML100` series，容量下界 `route_lb=17`，总需求 `total_demand=2034`。
  - 统计特征：`demand_cv=1.4178`，`distance_cv=0.4721`，`nn_cv=0.5369`，`depot_distance_cv=0.3738`

- `cvrp2lib_XML100_3211_19`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_3211_19`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `34` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=3`，`directed_arcs=10100`
  - 参考值：`objective=47306`，`vehicles=34`
  - 数据特征：`XML100` series，容量下界 `route_lb=34`，总需求 `total_demand=100`。
  - 统计特征：`demand_cv=0`，`distance_cv=0.657`，`nn_cv=0.8212`，`depot_distance_cv=0.2809`

- `cvrp2lib_XML100_3212_09`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_3212_09`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `15` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=7`，`directed_arcs=10100`
  - 参考值：`objective=18248`，`vehicles=15`
  - 数据特征：`XML100` series，容量下界 `route_lb=15`，总需求 `total_demand=100`。
  - 统计特征：`demand_cv=0`，`distance_cv=0.6162`，`nn_cv=1.0985`，`depot_distance_cv=0.2258`

- `cvrp2lib_XML100_3213_22`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_3213_22`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `10` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=11`，`directed_arcs=10100`
  - 参考值：`objective=16913`，`vehicles=10`
  - 数据特征：`XML100` series，容量下界 `route_lb=10`，总需求 `total_demand=100`。
  - 统计特征：`demand_cv=0`，`distance_cv=0.9575`，`nn_cv=1.2005`，`depot_distance_cv=0.1359`

- `cvrp2lib_XML100_3224_14`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_3224_14`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `8` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=84`，`directed_arcs=10100`
  - 参考值：`objective=14333`，`vehicles=8`
  - 数据特征：`XML100` series，容量下界 `route_lb=8`，总需求 `total_demand=606`。
  - 统计特征：`demand_cv=0.4747`，`distance_cv=0.6241`，`nn_cv=0.8221`，`depot_distance_cv=0.2895`

- `cvrp2lib_XML100_3231_15`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_3231_15`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `29` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=27`，`directed_arcs=10100`
  - 参考值：`objective=56790`，`vehicles=29`
  - 数据特征：`XML100` series，容量下界 `route_lb=29`，总需求 `total_demand=767`。
  - 统计特征：`demand_cv=0.2086`，`distance_cv=0.5533`，`nn_cv=0.8171`，`depot_distance_cv=0.2545`

- `cvrp2lib_XML100_3234_01`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_3234_01`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `7` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=121`，`directed_arcs=10100`
  - 参考值：`objective=9773`，`vehicles=7`
  - 数据特征：`XML100` series，容量下界 `route_lb=7`，总需求 `total_demand=777`。
  - 统计特征：`demand_cv=0.2129`，`distance_cv=0.7238`，`nn_cv=1.6123`，`depot_distance_cv=0.6532`

- `cvrp2lib_XML100_3243_22`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_3243_22`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `10` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=550`，`directed_arcs=10100`
  - 参考值：`objective=18458`，`vehicles=10`
  - 数据特征：`XML100` series，容量下界 `route_lb=10`，总需求 `total_demand=5275`。
  - 统计特征：`demand_cv=0.4916`，`distance_cv=0.7427`，`nn_cv=0.7042`，`depot_distance_cv=0.1087`

- `cvrp2lib_XML100_3243_24`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_3243_24`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `9` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=585`，`directed_arcs=10100`
  - 参考值：`objective=16388`，`vehicles=9`
  - 数据特征：`XML100` series，容量下界 `route_lb=9`，总需求 `total_demand=5081`。
  - 统计特征：`demand_cv=0.5804`，`distance_cv=0.645`，`nn_cv=0.8097`，`depot_distance_cv=0.246`

- `cvrp2lib_XML100_3246_14`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_3246_14`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `3` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=2304`，`directed_arcs=10100`
  - 参考值：`objective=6169`，`vehicles=3`
  - 数据特征：`XML100` series，容量下界 `route_lb=3`，总需求 `total_demand=5215`。
  - 统计特征：`demand_cv=0.5335`，`distance_cv=0.6419`，`nn_cv=1.0106`，`depot_distance_cv=0.2531`

- `cvrp2lib_XML100_3261_01`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_3261_01`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `32` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=141`，`directed_arcs=10100`
  - 参考值：`objective=49951`，`vehicles=32`
  - 数据特征：`XML100` series，容量下界 `route_lb=31`，总需求 `total_demand=4333`。
  - 统计特征：`demand_cv=0.615`，`distance_cv=0.6593`，`nn_cv=0.9067`，`depot_distance_cv=0.3435`

- `cvrp2lib_XML100_3274_16`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_3274_16`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `8` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=155`，`directed_arcs=10100`
  - 参考值：`objective=10876`，`vehicles=8`
  - 数据特征：`XML100` series，容量下界 `route_lb=8`，总需求 `total_demand=1211`。
  - 统计特征：`demand_cv=1.6987`，`distance_cv=0.7245`，`nn_cv=0.8161`，`depot_distance_cv=0.6486`

- `cvrp2lib_XML100_3312_14`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_3312_14`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `17` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=6`，`directed_arcs=10100`
  - 参考值：`objective=28714`，`vehicles=17`
  - 数据特征：`XML100` series，容量下界 `route_lb=17`，总需求 `total_demand=100`。
  - 统计特征：`demand_cv=0`，`distance_cv=0.5079`，`nn_cv=0.7421`，`depot_distance_cv=0.3299`

- `cvrp2lib_XML100_3316_22`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_3316_22`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `3` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=45`，`directed_arcs=10100`
  - 参考值：`objective=8993`，`vehicles=3`
  - 数据特征：`XML100` series，容量下界 `route_lb=3`，总需求 `total_demand=100`。
  - 统计特征：`demand_cv=0`，`distance_cv=0.5117`，`nn_cv=0.7061`，`depot_distance_cv=0.371`

- `cvrp2lib_XML100_3341_13`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_3341_13`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `24` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=209`，`directed_arcs=10100`
  - 参考值：`objective=41113`，`vehicles=24`
  - 数据特征：`XML100` series，容量下界 `route_lb=24`，总需求 `total_demand=4908`。
  - 统计特征：`demand_cv=0.6279`，`distance_cv=0.5075`，`nn_cv=0.6759`，`depot_distance_cv=0.3448`

- `cvrp2lib_XML100_3346_25`
  - 问题描述：CVRP2LIB CVRP_XML 实例 `XML100_3346_25`，从一个 depot 出发为 `100` 个客户设计容量受限车辆路线；输入不固定车辆数，参考解给出使用车辆数 `3` 和总距离。
  - 规模：`nodes=101`，`customers=100`，`vehicles=null`，`capacity=2196`，`directed_arcs=10100`
  - 参考值：`objective=8717`，`vehicles=3`
  - 数据特征：`XML100` series，容量下界 `route_lb=3`，总需求 `total_demand=5116`。
  - 统计特征：`demand_cv=0.5761`，`distance_cv=0.516`，`nn_cv=0.6428`，`depot_distance_cv=0.374`


## 问题定义

每个 case 都是在给定一个 depot、若干客户、客户需求、车辆容量和节点间距离度量的前提下，寻找若干条车辆路线。每条路线从 depot 出发并回到 depot，每个客户恰好被访问一次，任一路线上的客户需求总和不能超过车辆容量。

与 `cvrplib/cvrp` 的固定车辆数 CVRP 口径不同，CVRP_XML 输入中不提供固定车辆数。参考解同时给出使用的车辆数和总路线距离，因此后续建模时应显式区分输入车辆数为空、参考解车辆数可用这两个事实。
