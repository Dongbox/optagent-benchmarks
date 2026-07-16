# QAPLIB 数据来源说明

QAPLIB 目录保存来自 QAPLIB 的 quadratic assignment benchmark case。当前是二次分配问题，用于测试 OptAgent 在 permutation / sequence 优化问题上的表现。

数据集来源：

- QAPLIB 主页：https://qaplib.mgi.polymtl.ca
- 完整公开数据归档：https://doi.org/10.7488/ds/3428

本地完整数据集缓存保存在：

```text
benchmarks/cases/qaplib/quadratic_assignment/raw/
```

正式注册 case 的 `.dat` 和 `.sln` 文件位于 `quadratic_assignment/raw/` 根层，保证 `--no-download` 时可直接运行；未注册的完整数据集仅作为受控下载缓存，不属于 README 的 case 清单。

## 矩阵顺序说明

QAPLIB `.dat` 文件按原始顺序提供两个 `n x n` 矩阵。当前 benchmark loader 保留该顺序，并按 `sum A[i][j] * B[p[i]][p[j]]` 计算目标值；代码中的 `flow` 和 `distance` 命名不保证反映每个实例中两个矩阵的真实语义。

在当前“只用于测试模型优化能力”的 benchmark 需求下，两个矩阵分别称为 flow 或 distance 不影响最终优化结果：交换两个矩阵会得到等价的排列优化问题，最优目标值保持一致，只是对应的最优置换表示会变为逆映射。注意，这并不表示同一个置换在交换矩阵后 cost 一定相同。

## 相关 case

### smoke

- `qaplib_chr12a`
  - 问题描述：12 设施/12 位置的 quadratic assignment 问题。
  - 规模：`facilities=12`，`locations=12`
  - 参考值：`objective=9552`
  - 数据特征：稀疏关系矩阵配稠密权重矩阵，代表小规模 sparse/dense 结构。
- `qaplib_had12`
  - 问题描述：12 设施/12 位置的 quadratic assignment 问题。
  - 规模：`facilities=12`，`locations=12`
  - 参考值：`objective=1652`
  - 数据特征：两个矩阵都较稠密且数值均衡，用作小规模基础 sanity 样本。
- `qaplib_nug12`
  - 问题描述：12 设施/12 位置的 quadratic assignment 问题。
  - 规模：`facilities=12`，`locations=12`
  - 参考值：`objective=578`
  - 数据特征：经典 Nugent 小规模实例，距离结构规整、交互矩阵中等稀疏。
- `qaplib_scr12`
  - 问题描述：12 设施/12 位置的 quadratic assignment 问题。
  - 规模：`facilities=12`，`locations=12`
  - 参考值：`objective=31410`
  - 数据特征：数值跨度明显，补充小规模高权重差异样本。
- `qaplib_tai12b`
  - 问题描述：12 设施/12 位置的 quadratic assignment 问题。
  - 规模：`facilities=12`，`locations=12`
  - 参考值：`objective=39464925`
  - 数据特征：Taillard b 型非对称/不均衡矩阵，目标值尺度大。
- `qaplib_esc16b`
  - 问题描述：16 设施/16 位置的 quadratic assignment 问题。
  - 规模：`facilities=16`，`locations=16`
  - 参考值：`objective=292`
  - 数据特征：ESC 小规模 mixed/mixed 结构，轻量但不同于 Nugent/Hadley 系列。
- `qaplib_esc16h`
  - 问题描述：16 设施/16 位置的 quadratic assignment 问题。
  - 规模：`facilities=16`，`locations=16`
  - 参考值：`objective=996`
  - 数据特征：ESC dense/mixed 结构，比 `esc16b` 更有搜索压力。

### calibration

- `qaplib_els19`
  - 问题描述：19 设施/19 位置的 quadratic assignment 问题。
  - 规模：`facilities=19`，`locations=19`
  - 参考值：`objective=17212548`
  - 数据特征：第二矩阵高度稀疏且含大惩罚值，补充极端权重样本。
- `qaplib_had20`
  - 问题描述：20 设施/20 位置的 quadratic assignment 问题。
  - 规模：`facilities=20`，`locations=20`
  - 参考值：`objective=6922`
  - 数据特征：稠密、对称、数值均衡的中小规模校准样本。
- `qaplib_lipa20a`
  - 问题描述：20 设施/20 位置的 quadratic assignment 问题。
  - 规模：`facilities=20`，`locations=20`
  - 参考值：`objective=3683`
  - 数据特征：LIPA a 型结构，一个矩阵接近常量/低变异，适合测试易解结构。
- `qaplib_lipa20b`
  - 问题描述：20 设施/20 位置的 quadratic assignment 问题。
  - 规模：`facilities=20`，`locations=20`
  - 参考值：`objective=27076`
  - 数据特征：LIPA b 型结构，与 a 型同规模但矩阵平衡度不同，保留成对对照。
- `qaplib_nug20`
  - 问题描述：20 设施/20 位置的 quadratic assignment 问题。
  - 规模：`facilities=20`，`locations=20`
  - 参考值：`objective=2570`
  - 数据特征：经典 Nugent 20 维实例，距离规整、交互矩阵中等稀疏。
- `qaplib_scr20`
  - 问题描述：20 设施/20 位置的 quadratic assignment 问题。
  - 规模：`facilities=20`，`locations=20`
  - 参考值：`objective=110030`
  - 数据特征：稀疏/稠密组合且数值跨度大，补充高目标尺度样本。
- `qaplib_tai20b`
  - 问题描述：20 设施/20 位置的 quadratic assignment 问题。
  - 规模：`facilities=20`，`locations=20`
  - 参考值：`objective=122455319`
  - 数据特征：Taillard b 型非对称 mixed 结构，目标值尺度很大。
- `qaplib_chr25a`
  - 问题描述：25 设施/25 位置的 quadratic assignment 问题。
  - 规模：`facilities=25`，`locations=25`
  - 参考值：`objective=3796`
  - 数据特征：CHR 稀疏结构中保留的较大代表，搜索 gap 对轻预算较敏感。
- `qaplib_bur26a`
  - 问题描述：26 设施/26 位置的 quadratic assignment 问题。
  - 规模：`facilities=26`，`locations=26`
  - 参考值：`objective=5426670`
  - 数据特征：Burkard 26 维同系列代表，稠密/混合且行和较均衡。
- `qaplib_bur26g`
  - 问题描述：26 设施/26 位置的 quadratic assignment 问题。
  - 规模：`facilities=26`，`locations=26`
  - 参考值：`objective=10117172`
  - 数据特征：Burkard 26 维中更高惩罚尺度代表，避免只保留低尺度近邻。
- `qaplib_kra30a`
  - 问题描述：30 设施/30 位置的 quadratic assignment 问题。
  - 规模：`facilities=30`，`locations=30`
  - 参考值：`objective=88900`
  - 数据特征：Krarup 结构，稠密矩阵配较稀疏权重矩阵，补充 30 维校准样本。
- `qaplib_tai30a`
  - 问题描述：30 设施/30 位置的 quadratic assignment 问题。
  - 规模：`facilities=30`，`locations=30`
  - 参考值：`objective=1818146`
  - 数据特征：Taillard a 型稠密均衡结构，和 b 型形成对照。
- `qaplib_tai30b`
  - 问题描述：30 设施/30 位置的 quadratic assignment 问题。
  - 规模：`facilities=30`，`locations=30`
  - 参考值：`objective=637117113`
  - 数据特征：Taillard b 型非对称 mixed 结构，目标值尺度和矩阵不均衡度更高。
- `qaplib_tho30`
  - 问题描述：30 设施/30 位置的 quadratic assignment 问题。
  - 规模：`facilities=30`，`locations=30`
  - 参考值：`objective=149936`
  - 数据特征：Tho 系列中等规模代表，第二矩阵约半稀疏且数值跨度较大。

### full

- `qaplib_esc32e`
  - 问题描述：32 设施/32 位置的 quadratic assignment 问题。
  - 规模：`facilities=32`，`locations=32`
  - 参考值：`objective=2`
  - 数据特征：ESC 32 维有参考解的稀疏代表，最优值很小，适合观察 gap 表现。
- `qaplib_kra32`
  - 问题描述：32 设施/32 位置的 quadratic assignment 问题。
  - 规模：`facilities=32`，`locations=32`
  - 参考值：`objective=88900`
  - 数据特征：Krarup 稀疏/稠密组合，与 `kra30a` 相近但规模略增。
- `qaplib_tai35a`
  - 问题描述：35 设施/35 位置的 quadratic assignment 问题。
  - 规模：`facilities=35`，`locations=35`
  - 参考值：`objective=2422002`
  - 数据特征：Taillard a 型 full 层入口，稠密均衡矩阵。
- `qaplib_tai35b`
  - 问题描述：35 设施/35 位置的 quadratic assignment 问题。
  - 规模：`facilities=35`，`locations=35`
  - 参考值：`objective=283315445`
  - 数据特征：Taillard b 型 full 层入口，非对称 mixed 结构且目标尺度大。
- `qaplib_ste36c`
  - 问题描述：36 设施/36 位置的 quadratic assignment 问题。
  - 规模：`facilities=36`，`locations=36`
  - 参考值：`objective=8239110`
  - 数据特征：STE 系列高数值跨度代表；同系列 `ste36a` 轻测出错，因此保留 `ste36c`。
- `qaplib_lipa40a`
  - 问题描述：40 设施/40 位置的 quadratic assignment 问题。
  - 规模：`facilities=40`，`locations=40`
  - 参考值：`objective=31538`
  - 数据特征：LIPA a 型 40 维代表，低变异结构，轻预算容易接近最优。
- `qaplib_lipa40b`
  - 问题描述：40 设施/40 位置的 quadratic assignment 问题。
  - 规模：`facilities=40`，`locations=40`
  - 参考值：`objective=476581`
  - 数据特征：LIPA b 型 40 维代表，与 a 型同规模但目标尺度和结构不同。
- `qaplib_tho40`
  - 问题描述：40 设施/40 位置的 quadratic assignment 问题。
  - 规模：`facilities=40`，`locations=40`
  - 参考值：`objective=240516`
  - 数据特征：Tho 系列 full 层代表，第二矩阵较稀疏且数值跨度明显。
- `qaplib_sko42`
  - 问题描述：42 设施/42 位置的 quadratic assignment 问题。
  - 规模：`facilities=42`，`locations=42`
  - 参考值：`objective=15812`
  - 数据特征：Sko 系列 full 层小规模代表，规整稠密/混合结构。
- `qaplib_wil50`
  - 问题描述：50 设施/50 位置的 quadratic assignment 问题。
  - 规模：`facilities=50`，`locations=50`
  - 参考值：`objective=48816`
  - 数据特征：Wilhelm 50 维代表，稠密且较均衡，作为 50 维质量对照。
- `qaplib_tai50b`
  - 问题描述：50 设施/50 位置的 quadratic assignment 问题。
  - 规模：`facilities=50`，`locations=50`
  - 参考值：`objective=458821517`
  - 数据特征：Taillard b 型 50 维非对称 mixed 结构，保留中大规模困难样本。
- `qaplib_sko64`
  - 问题描述：64 设施/64 位置的 quadratic assignment 问题。
  - 规模：`facilities=64`，`locations=64`
  - 参考值：`objective=48498`
  - 数据特征：Sko 系列 64 维代表，规模提升但结构仍较规整。
- `qaplib_tai64c`
  - 问题描述：64 设施/64 位置的 quadratic assignment 问题。
  - 规模：`facilities=64`，`locations=64`
  - 参考值：`objective=1855928`
  - 数据特征：稀疏/高惩罚结构，和常规 TAI a/b、SKO 样本差异明显。
- `qaplib_tai80b`
  - 问题描述：80 设施/80 位置的 quadratic assignment 问题。
  - 规模：`facilities=80`，`locations=80`
  - 参考值：`objective=818415043`
  - 数据特征：Taillard b 型 80 维代表，是 full 层最大且较困难的非对称样本。

### pressure

- `qaplib_lipa90a`
  - 问题描述：90 设施/90 位置的 quadratic assignment 问题。
  - 规模：`facilities=90`，`locations=90`
  - 参考值：`objective=360630`
  - 数据特征：LIPA a 型 pressure 代表，低变异结构，适合观察大规模易结构表现。
- `qaplib_lipa90b`
  - 问题描述：90 设施/90 位置的 quadratic assignment 问题。
  - 规模：`facilities=90`，`locations=90`
  - 参考值：`objective=12490441`
  - 数据特征：LIPA b 型 pressure 代表，与 a 型同规模形成结构对照。
- `qaplib_sko100a`
  - 问题描述：100 设施/100 位置的 quadratic assignment 问题。
  - 规模：`facilities=100`，`locations=100`
  - 参考值：`objective=152002`
  - 数据特征：Sko 100 维系列代表；同系列 `sko100b-f` 近似度高，保留一个代表。
- `qaplib_tai100a`
  - 问题描述：100 设施/100 位置的 quadratic assignment 问题。
  - 规模：`facilities=100`，`locations=100`
  - 参考值：`objective=21052466`
  - 数据特征：Taillard a 型 100 维稠密均衡结构，pressure 层标准样本。
- `qaplib_tai100b`
  - 问题描述：100 设施/100 位置的 quadratic assignment 问题。
  - 规模：`facilities=100`，`locations=100`
  - 参考值：`objective=1185996137`
  - 数据特征：Taillard b 型 100 维非对称 mixed 结构，目标尺度大、搜索压力高。
- `qaplib_wil100`
  - 问题描述：100 设施/100 位置的 quadratic assignment 问题。
  - 规模：`facilities=100`，`locations=100`
  - 参考值：`objective=273038`
  - 数据特征：Wilhelm 100 维代表，稠密且较均衡，作为 pressure 层质量对照。
- `qaplib_esc128`
  - 问题描述：128 设施/128 位置的 quadratic assignment 问题。
  - 规模：`facilities=128`，`locations=128`
  - 参考值：`objective=64`
  - 数据特征：ESC 大规模稀疏结构，最优值很小，能暴露 gap 归一化和稀疏搜索表现。
- `qaplib_tho150`
  - 问题描述：150 设施/150 位置的 quadratic assignment 问题。
  - 规模：`facilities=150`，`locations=150`
  - 参考值：`objective=8133398`
  - 数据特征：Tho 150 维大规模 mixed 结构，是当前正式 pressure 中最大样本。

## 问题定义

每个 case 都是在给定两个权重矩阵的前提下，寻找设施到位置的最优置换，使总分配成本最小。
