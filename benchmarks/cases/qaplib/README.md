# QAPLIB 数据来源说明

QAPLIB 目录保存来自 QAPLIB 的 quadratic assignment benchmark case。当前是二次分配问题，用于测试 OptAgent 在 permutation / sequence 优化问题上的表现。

## 数据来源说明

QAPLIB（Quadratic Assignment Problem Library）是二次分配问题基准库，提供标准实例和公开参考解，用于评估排列优化算法。

数据集来源网站：

- QAPLIB 主页：https://qaplib.mgi.polymtl.ca
- QAPLIB 数据归档：https://doi.org/10.7488/ds/3428
- 本地实例目录：`benchmarks/cases/qaplib/quadratic_assignment/raw/`

## 问题说明

给定两个 n×n 矩阵，寻找设施到位置的一个置换，使二次分配成本最小：

```text
cost(p) = sum(i, j, A[i][j] * B[p[i]][p[j]])
```

每个设施和位置都必须恰好使用一次，目标是最小化总分配成本。

## 数据筛选依据

规模定义：

- `facilities`：设施数量；
- `locations`：位置数量，当前与 facilities 相同；
- 核心规模指标为 n，即矩阵维度。

tier 分类范围：

| tier | case 数量 | n 范围 |
|---|---:|---:|
| smoke | 20 | 10–18 |
| calibration | 20 | 19–31 |
| full | 15 | 32–89 |
| pressure | 10 | 90–150 |

筛选策略：将每个算例表示为由 n、流量/距离矩阵的非零比例、归一化分布分位数与离散度、行和不均衡、对称性、谱结构以及两矩阵相关性组成的特征向量。在同一 tier 的完整候选集内对各维做 z-score 标准化，以此后特征向量的欧氏距离度量算例近似程度。

## 建模说明

建模方式：使用 `sequence_var` 表示设施到位置的置换，通过 external callback 计算二次分配目标值，属于 permutation blackbox 模型。

适用的求解方式：

- `solve()`：适用；
- `solve_cpsat()`：当前不适用；
- `solve_milp()`：当前不适用，尚未提供 external callback 到 MILP 的 lowering。

## 特殊备注

- `.dat` 文件包含实例维度和两个 n×n 矩阵，`.sln` 文件提供参考目标值和置换信息。
- 当前正式注册的参考值均为公开最优值。

## 相关 case

### smoke

- `qaplib_chr12a`
  - 问题描述：12 个设施分配到 12 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=12`，`locations=12`
  - 参考值性质：最优
  - 参考值/区间：`objective=9552`
  - 备注：无

- `qaplib_had12`
  - 问题描述：12 个设施分配到 12 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=12`，`locations=12`
  - 参考值性质：最优
  - 参考值/区间：`objective=1652`
  - 备注：无

- `qaplib_nug12`
  - 问题描述：12 个设施分配到 12 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=12`，`locations=12`
  - 参考值性质：最优
  - 参考值/区间：`objective=578`
  - 备注：无

- `qaplib_rou12`
  - 问题描述：12 个设施分配到 12 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=12`，`locations=12`
  - 参考值性质：最优
  - 参考值/区间：`objective=235528`
  - 备注：无

- `qaplib_scr12`
  - 问题描述：12 个设施分配到 12 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=12`，`locations=12`
  - 参考值性质：最优
  - 参考值/区间：`objective=31410`
  - 备注：无

- `qaplib_tai12a`
  - 问题描述：12 个设施分配到 12 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=12`，`locations=12`
  - 参考值性质：最优
  - 参考值/区间：`objective=224416`
  - 备注：无

- `qaplib_tai12b`
  - 问题描述：12 个设施分配到 12 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=12`，`locations=12`
  - 参考值性质：最优
  - 参考值/区间：`objective=39464925`
  - 备注：无

- `qaplib_nug14`
  - 问题描述：14 个设施分配到 14 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=14`，`locations=14`
  - 参考值性质：最优
  - 参考值/区间：`objective=1014`
  - 备注：无

- `qaplib_chr15a`
  - 问题描述：15 个设施分配到 15 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=15`，`locations=15`
  - 参考值性质：最优
  - 参考值/区间：`objective=9896`
  - 备注：无

- `qaplib_rou15`
  - 问题描述：15 个设施分配到 15 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=15`，`locations=15`
  - 参考值性质：最优
  - 参考值/区间：`objective=354210`
  - 备注：无

- `qaplib_scr15`
  - 问题描述：15 个设施分配到 15 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=15`，`locations=15`
  - 参考值性质：最优
  - 参考值/区间：`objective=51140`
  - 备注：无

- `qaplib_tai15b`
  - 问题描述：15 个设施分配到 15 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=15`，`locations=15`
  - 参考值性质：最优
  - 参考值/区间：`objective=51765268`
  - 备注：无

- `qaplib_esc16b`
  - 问题描述：16 个设施分配到 16 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=16`，`locations=16`
  - 参考值性质：最优
  - 参考值/区间：`objective=292`
  - 备注：无

- `qaplib_esc16c`
  - 问题描述：16 个设施分配到 16 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=16`，`locations=16`
  - 参考值性质：最优
  - 参考值/区间：`objective=160`
  - 备注：无

- `qaplib_esc16d`
  - 问题描述：16 个设施分配到 16 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=16`，`locations=16`
  - 参考值性质：最优
  - 参考值/区间：`objective=16`
  - 备注：无

- `qaplib_esc16f`
  - 问题描述：16 个设施分配到 16 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=16`，`locations=16`
  - 参考值性质：最优
  - 参考值/区间：`objective=0`
  - 备注：无

- `qaplib_esc16h`
  - 问题描述：16 个设施分配到 16 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=16`，`locations=16`
  - 参考值性质：最优
  - 参考值/区间：`objective=996`
  - 备注：无

- `qaplib_esc16j`
  - 问题描述：16 个设施分配到 16 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=16`，`locations=16`
  - 参考值性质：最优
  - 参考值/区间：`objective=8`
  - 备注：无

- `qaplib_had16`
  - 问题描述：16 个设施分配到 16 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=16`，`locations=16`
  - 参考值性质：最优
  - 参考值/区间：`objective=3720`
  - 备注：无

- `qaplib_nug16a`
  - 问题描述：16 个设施分配到 16 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=16`，`locations=16`
  - 参考值性质：最优
  - 参考值/区间：`objective=1610`
  - 备注：无

### calibration

- `qaplib_els19`
  - 问题描述：19 个设施分配到 19 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=19`，`locations=19`
  - 参考值性质：最优
  - 参考值/区间：`objective=17212548`
  - 备注：无

- `qaplib_chr20b`
  - 问题描述：20 个设施分配到 20 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=20`，`locations=20`
  - 参考值性质：最优
  - 参考值/区间：`objective=2298`
  - 备注：无

- `qaplib_chr20c`
  - 问题描述：20 个设施分配到 20 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=20`，`locations=20`
  - 参考值性质：最优
  - 参考值/区间：`objective=14142`
  - 备注：无

- `qaplib_had20`
  - 问题描述：20 个设施分配到 20 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=20`，`locations=20`
  - 参考值性质：最优
  - 参考值/区间：`objective=6922`
  - 备注：无

- `qaplib_lipa20a`
  - 问题描述：20 个设施分配到 20 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=20`，`locations=20`
  - 参考值性质：最优
  - 参考值/区间：`objective=3683`
  - 备注：无

- `qaplib_lipa20b`
  - 问题描述：20 个设施分配到 20 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=20`，`locations=20`
  - 参考值性质：最优
  - 参考值/区间：`objective=27076`
  - 备注：无

- `qaplib_nug20`
  - 问题描述：20 个设施分配到 20 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=20`，`locations=20`
  - 参考值性质：最优
  - 参考值/区间：`objective=2570`
  - 备注：无

- `qaplib_rou20`
  - 问题描述：20 个设施分配到 20 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=20`，`locations=20`
  - 参考值性质：最优
  - 参考值/区间：`objective=725522`
  - 备注：无

- `qaplib_scr20`
  - 问题描述：20 个设施分配到 20 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=20`，`locations=20`
  - 参考值性质：最优
  - 参考值/区间：`objective=110030`
  - 备注：无

- `qaplib_tai20b`
  - 问题描述：20 个设施分配到 20 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=20`，`locations=20`
  - 参考值性质：最优
  - 参考值/区间：`objective=122455319`
  - 备注：无

- `qaplib_chr25a`
  - 问题描述：25 个设施分配到 25 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=25`，`locations=25`
  - 参考值性质：最优
  - 参考值/区间：`objective=3796`
  - 备注：无

- `qaplib_bur26a`
  - 问题描述：26 个设施分配到 26 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=26`，`locations=26`
  - 参考值性质：最优
  - 参考值/区间：`objective=5426670`
  - 备注：无

- `qaplib_nug28`
  - 问题描述：28 个设施分配到 28 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=28`，`locations=28`
  - 参考值性质：最优
  - 参考值/区间：`objective=5166`
  - 备注：无

- `qaplib_kra30a`
  - 问题描述：30 个设施分配到 30 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=30`，`locations=30`
  - 参考值性质：最优
  - 参考值/区间：`objective=88900`
  - 备注：无

- `qaplib_lipa30a`
  - 问题描述：30 个设施分配到 30 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=30`，`locations=30`
  - 参考值性质：最优
  - 参考值/区间：`objective=13178`
  - 备注：无

- `qaplib_lipa30b`
  - 问题描述：30 个设施分配到 30 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=30`，`locations=30`
  - 参考值性质：最优
  - 参考值/区间：`objective=151426`
  - 备注：无

- `qaplib_nug30`
  - 问题描述：30 个设施分配到 30 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=30`，`locations=30`
  - 参考值性质：最优
  - 参考值/区间：`objective=6124`
  - 备注：无

- `qaplib_tai30a`
  - 问题描述：30 个设施分配到 30 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=30`，`locations=30`
  - 参考值性质：最优
  - 参考值/区间：`objective=1818146`
  - 备注：无

- `qaplib_tai30b`
  - 问题描述：30 个设施分配到 30 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=30`，`locations=30`
  - 参考值性质：最优
  - 参考值/区间：`objective=637117113`
  - 备注：无

- `qaplib_tho30`
  - 问题描述：30 个设施分配到 30 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=30`，`locations=30`
  - 参考值性质：最优
  - 参考值/区间：`objective=149936`
  - 备注：无

### full

- `qaplib_esc32e`
  - 问题描述：32 个设施分配到 32 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=32`，`locations=32`
  - 参考值性质：最优
  - 参考值/区间：`objective=2`
  - 备注：无

- `qaplib_kra32`
  - 问题描述：32 个设施分配到 32 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=32`，`locations=32`
  - 参考值性质：最优
  - 参考值/区间：`objective=88700`
  - 备注：无

- `qaplib_tai35a`
  - 问题描述：35 个设施分配到 35 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=35`，`locations=35`
  - 参考值性质：最优
  - 参考值/区间：`objective=2422002`
  - 备注：无

- `qaplib_tai35b`
  - 问题描述：35 个设施分配到 35 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=35`，`locations=35`
  - 参考值性质：最优
  - 参考值/区间：`objective=283315445`
  - 备注：无

- `qaplib_ste36c`
  - 问题描述：36 个设施分配到 36 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=36`，`locations=36`
  - 参考值性质：最优
  - 参考值/区间：`objective=8239110`
  - 备注：无

- `qaplib_lipa40a`
  - 问题描述：40 个设施分配到 40 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=40`，`locations=40`
  - 参考值性质：最优
  - 参考值/区间：`objective=31538`
  - 备注：无

- `qaplib_lipa40b`
  - 问题描述：40 个设施分配到 40 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=40`，`locations=40`
  - 参考值性质：最优
  - 参考值/区间：`objective=476581`
  - 备注：无

- `qaplib_tho40`
  - 问题描述：40 个设施分配到 40 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=40`，`locations=40`
  - 参考值性质：最优
  - 参考值/区间：`objective=240516`
  - 备注：无

- `qaplib_tai50b`
  - 问题描述：50 个设施分配到 50 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=50`，`locations=50`
  - 参考值性质：最优
  - 参考值/区间：`objective=458821517`
  - 备注：无

- `qaplib_wil50`
  - 问题描述：50 个设施分配到 50 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=50`，`locations=50`
  - 参考值性质：最优
  - 参考值/区间：`objective=48816`
  - 备注：无

- `qaplib_sko64`
  - 问题描述：64 个设施分配到 64 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=64`，`locations=64`
  - 参考值性质：最优
  - 参考值/区间：`objective=48498`
  - 备注：无

- `qaplib_tai64c`
  - 问题描述：64 个设施分配到 64 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=64`，`locations=64`
  - 参考值性质：最优
  - 参考值/区间：`objective=1855928`
  - 备注：无

- `qaplib_lipa80a`
  - 问题描述：80 个设施分配到 80 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=80`，`locations=80`
  - 参考值性质：最优
  - 参考值/区间：`objective=253195`
  - 备注：无

- `qaplib_tai80a`
  - 问题描述：80 个设施分配到 80 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=80`，`locations=80`
  - 参考值性质：最优
  - 参考值/区间：`objective=13499184`
  - 备注：无

- `qaplib_tai80b`
  - 问题描述：80 个设施分配到 80 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=80`，`locations=80`
  - 参考值性质：最优
  - 参考值/区间：`objective=818415043`
  - 备注：无

### pressure

- `qaplib_lipa90a`
  - 问题描述：90 个设施分配到 90 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=90`，`locations=90`
  - 参考值性质：最优
  - 参考值/区间：`objective=360630`
  - 备注：无

- `qaplib_lipa90b`
  - 问题描述：90 个设施分配到 90 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=90`，`locations=90`
  - 参考值性质：最优
  - 参考值/区间：`objective=12490441`
  - 备注：无

- `qaplib_sko100a`
  - 问题描述：100 个设施分配到 100 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=100`，`locations=100`
  - 参考值性质：最优
  - 参考值/区间：`objective=152002`
  - 备注：无

- `qaplib_sko100e`
  - 问题描述：100 个设施分配到 100 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=100`，`locations=100`
  - 参考值性质：最优
  - 参考值/区间：`objective=149150`
  - 备注：无

- `qaplib_tai100a`
  - 问题描述：100 个设施分配到 100 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=100`，`locations=100`
  - 参考值性质：最优
  - 参考值/区间：`objective=21052466`
  - 备注：无

- `qaplib_tai100b`
  - 问题描述：100 个设施分配到 100 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=100`，`locations=100`
  - 参考值性质：最优
  - 参考值/区间：`objective=1185996137`
  - 备注：无

- `qaplib_wil100`
  - 问题描述：100 个设施分配到 100 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=100`，`locations=100`
  - 参考值性质：最优
  - 参考值/区间：`objective=273038`
  - 备注：无

- `qaplib_esc128`
  - 问题描述：128 个设施分配到 128 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=128`，`locations=128`
  - 参考值性质：最优
  - 参考值/区间：`objective=64`
  - 备注：无

- `qaplib_tai150b`
  - 问题描述：150 个设施分配到 150 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=150`，`locations=150`
  - 参考值性质：最优
  - 参考值/区间：`objective=498896643`
  - 备注：无

- `qaplib_tho150`
  - 问题描述：150 个设施分配到 150 个位置的二次分配问题，目标是最小化二次分配成本。
  - 规模：`facilities=150`，`locations=150`
  - 参考值性质：最优
  - 参考值/区间：`objective=8133398`
  - 备注：无
