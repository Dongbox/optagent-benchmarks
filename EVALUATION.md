# 策略性能评估框架 (Strategy Performance Evaluation)

本文档说明 OptAgent 策略性能评估的设计哲学、证据链结构与计算规则。

当前统计实现入口是 [`telemetry_metrics.py`](telemetry_metrics.py)。它只接受
OptAgent canonical runtime telemetry（protobuf 或由 protobuf 生成的 JSON
projection），并从归一化 rows / curves 派生五维指标。旧
[`scoring.py`](scoring.py) 和 [`scoring_phase2.py`](scoring_phase2.py)
保留为历史回归资产，不再作为新 benchmark 统计链路的公开输入路径。
Dashboard 发布入口是 [`telemetry_artifacts.py`](telemetry_artifacts.py)，它
生成 `manifest.json`、`rows.jsonl`、`curves.jsonl`、`throughput.jsonl`、
`five_dimensional_metrics.json`、`statistical_tests.json` 和 `dashboard.json`。

---

## 评估哲学 (Evaluation Philosophy)

### 核心原则

现代启发式算法评估已经**放弃寻找类似 MIP Gap 的统一指标** [15]，而是采用**多维证据链（Evidence Chain）**来系统化地证明改进有效。

工业界优化算法 benchmark 回答三个问题：

1. **算法达到了什么结果？**（Outcome）
2. **用了多少资源？**（Efficiency）
3. **结果可靠吗？**（Robustness）

评分（Composite Score）只是基于这些证据生成的**便于排序的摘要指标**，可以随经验调整。真正具有长期价值的是**原始指标（Raw Metrics）**和**证据链（Evidence Chain）**。

### Effectiveness vs Efficiency 分离

Rankey & Nelson (2025) [15] 明确提出：应该将 **Effectiveness（结果好不好）** 和 **Efficiency（达到这个结果花了多少预算）** 彻底分开评估，而不是只看最终 objective。真正应该评价的是 **Quality × Cost**，其中 Cost 通常是 **Objective Evaluations** 或 **Runtime**。

这也是为什么 OptAgent 将 Outcome 和 Efficiency 作为独立的证据层，而不是混合为单一指标。

### Anytime Performance 的中心地位

Brockhoff et al. (2022) [16] 在黑盒优化基准测试综述中提出：

> **Runtime（达到目标质量所需预算）才是最具有通用意义的性能指标。**

不是最终目标值，而是**需要多少 Evaluation 才能达到 Target**。这种 **Anytime Performance Assessment** 已成为现代 Metaheuristic 评估的核心范式。

横轴通常使用 **Function Evaluations (FEs)** 而非时间，因为不同语言、机器、CPU 的时间不可比，而 Objective Evaluation 几乎所有优化问题都有 [16]。

### 工业标准参考

| 基准系统 | 评估方式 |
|---------|----------|
| **COCO** [1] | 固定目标性能下的 runtime/evaluations（ECDF curves），不预设权重 |
| **MiniZinc Challenge** [2] | Borda scoring + anytime penalty，强调 solver portfolio 比较 |
| **MIPLIB** [3] | Primal/dual integral、node throughput、time-to-target，原始日志公开 |
| **SCIP** [4] | Per-heuristic calls/success/time/improvement，透明化算子贡献 |
| **CP Profiler** [5] | Search tree visualization + diagnostic metrics，强调可解释性 |

OptAgent 采用类似设计：**canonical runtime telemetry → normalized rows /
curves → five-dimensional metrics → immutable artifacts → dashboard**。
Runtime 只产生 facts；gap、rank、robustness、anytime integral 和统计检验由
benchmark 层派生。Dashboard 只读取已发布 artifacts，不读取 runner 私有输出。

---

## 证据链 (Evidence Chain)

评估体系分四层：

```
┌─────────────────────────────────────────────────────┐
│  Outcome Metrics       │  最终解质量 + 可行性        │
├─────────────────────────────────────────────────────┤
│  Efficiency Metrics    │  Anytime + Runtime + Budget │
├─────────────────────────────────────────────────────┤
│  Robustness Metrics    │  Stability + 统计显著性      │
├─────────────────────────────────────────────────────┤
│  Search Diagnostics    │  Diversity + Operator + Trace│
└─────────────────────────────────────────────────────┘
```

**Composite Score（综合分）** 仅基于前三层计算，**Search Diagnostics 不参与评分**，而是作为解释性证据单独展示。

---

## 1. Outcome Metrics

衡量算法找到的解的**最终质量**。

### 1.1 Solution Quality (D1)

相对 gap 归一化为 0–100 分：

```
gap_rel = (objective - reference_cost) / |reference_cost|

quality_score = max(0, 100 × (1 - gap_rel / gap_threshold))
```

- **达到或优于参考解** (gap ≤ 0) → 100 分
- **gap 达到 threshold** → 0 分
- **不可行解** → 固定 0 分

**gap_threshold** 按问题组设定（基于工业 benchmark 文献）：

| 问题组 | gap_threshold | 依据 |
|--------|:-------------:|------|
| routing (TSP/VRP) | 0.20 | TSPLIB [6] / VRP benchmark [7] 中 20% gap 为中等表现 |
| scheduling | 0.50 | Job Shop benchmark [8] 中调度问题难度通常更高 |
| assignment (QAP) | 0.30 | QAPLIB [9] 中 QAP 中等难度实例的典型 gap |

### 1.2 Feasibility Rate

```
feasibility_rate = feasible_count / total_runs
```

不可行解占比反映约束处理能力。

### 1.3 Reference Cost

优先使用 **Best Known Solution (BKS)**；未知时使用 suite 内最佳解，标记 `reference_type: "relative"`。

---

## 2. Efficiency Metrics

衡量算法**达到目标所需的资源**。

### 2.1 Anytime Performance (D2)

评估搜索**全过程**的解质量，而非仅看最终值 [10]。

#### Primal Integral

```
primal_integral = ∫₀ᵀ gap(t) dt

其中 gap(t) = max(0, (incumbent(t) - reference_cost) / |reference_cost|)
```

incumbent(t) 为阶梯函数 — 仅在解改进时更新。

**归一化评分**：

```
max_integral = gap_threshold × T
anytime_score = max(0, 100 × (1 - primal_integral / max_integral))
```

Primal integral 最早用于 MIPLIB [3]，后成为 Metaheuristic benchmark 标配 [11]。

#### 扩展指标（Phase 2）

- **Incumbent Curve**：完整的 objective(t) 轨迹
- **Area Under Improvement Curve (AUIC)**：改进幅度积分
- **Time to X% of best**：达到最优解 X% 的时间

### 2.2 Runtime Efficiency (D3)

#### 当前实现：Throughput

```
evaluations_per_s = total_candidates_evaluated / wall_time_seconds

throughput_score = min(100, 100 × log₁₀(evaluations_per_s) / log₁₀(expected_throughput))
```

使用对数尺度，因为不同算子的 evaluation 成本差异巨大（GA: ~100μs/eval，CP Repair: ~50ms/eval）。

#### Phase 2 扩展（参考 COCO [1]）

| 指标 | 含义 | 重要性 |
|------|------|--------|
| **Time to Best** | 找到最优解的时间 | 反映早期收敛能力 |
| **Evaluations to Best** | 找到最优解的评估次数 | 独立于硬件的效率度量 |
| **Time to Target** | 达到预设目标（如 95% BKS）的时间 | COCO 标准指标 [1] |
| **Evaluations to Target** | 达到预设目标的评估次数 | 跨算法公平比较 |
| **Budget Efficiency** | 固定预算下的目标达成率 | 工业场景常用 |

**为什么不只看 throughput？**

不同 evaluation 成本完全不同。例如：
- GA offspring evaluation: ~100μs
- ALNS destroy-repair: ~10ms
- CP propagation: ~1ms

直接比较 eval/s 不公平。真正重要的是**达到目标所需的资源**（time-to-target / evaluations-to-target），这也是 COCO benchmark [1] 的核心设计。

### 2.3 Expected Throughput (基准)

| 问题组 | 基准 (eval/s) | 依据 |
|--------|:-------------:|------|
| routing | 100,000 | 中等规模 TSP/VRP（release 构建） |
| scheduling | 10,000 | 调度问题计算密集 |
| assignment | 50,000 | QAP 中等 |

---

## 3. Robustness Metrics

衡量算法在**多次运行**中的一致性和统计显著性。

### 3.1 Stability (D4)

最少需要 **5 个 seed**；发布级评分建议 **≥30 seeds** [12]。

```
stability_score = min(100, 0.5×consistency + 0.3×feasibility + 0.2×worst_case)
```

#### 3.1.1 解质量一致性 (CV-based)

```
cv = std(objectives) / |mean(objectives)|
consistency_score = max(0, 100 × (1 - cv / cv_threshold))
```

`cv_threshold` = 0.15 — 工业求解器的合理变异系数上界 [13]。

#### 3.1.2 可行性率

```
feasibility_score = feasible_count / total_runs × 100
```

#### 3.1.3 最差情况控制

```
worst_gap = (worst_objective - reference_cost) / |reference_cost|
worst_case_score = max(0, 100 × (1 - worst_gap / gap_threshold))
```

### 3.2 统计显著性 (Phase 2)

工业论文标配 [14]：

| 检验 | 用途 | 实现 |
|------|------|------|
| **Wilcoxon Signed-Rank** | 两策略配对比较 | scipy.stats.wilcoxon |
| **Friedman Test** | 多策略多实例比较 | scipy.stats.friedman |
| **Effect Size (Cohen's d)** | 差异实际大小 | (mean1 - mean2) / pooled_std |

以后 GA 提升 0.8%，直接输出 `p < 0.05, d = 0.42`，结束随机性质疑。

---

## 4. Search Diagnostics

**这一层不参与 Composite Score 计算**，而是作为**解释性证据**，帮助理解搜索行为和调参。

### 4.1 Diversity

```
diversity_at_termination ∈ [0, 1]
```

- **0** = 种群完全收敛（信息量丧失）
- **0.5+** = 健康范围
- **0.9+** = 可能未收敛（ALNS 常见）

**不是越高越好**。GA 后期 diversity = 0.05 可能是正常收敛；ALNS diversity = 0.7 可能说明根本没收敛。

### 4.2 Stagnation

```
stagnation_ratio = unimproved_iterations / total_iterations
```

80% 以上迭代无改进 → 可能需要更激进的 destroy 或 restart。

### 4.3 Termination Quality

| termination_reason | 含义 |
|:---|:---|
| `converged` / `optimal` | 算法自主判定最优或收敛 |
| `diversity_exhausted` | 种群多样性耗尽（正常） |
| `time_limit` | 时间预算耗尽 |
| `iteration_limit` | 迭代预算耗尽 |
| `stagnation` | 停滞检测触发 |

### 4.4 Operator Contribution (Phase 2)

**这是 OptAgent 最大优势**，商业 solver（如 SCIP [4]）都会输出 heuristic statistics。

| 指标 | 含义 |
|------|------|
| **Operator Calls** | 各算子调用次数 |
| **Acceptance Rate** | 各算子被接受的比例 |
| **Improvement Rate** | 各算子产生改进的比例 |
| **Average Delta** | 各算子平均改进幅度 |
| **Cumulative Contribution** | 各算子累计贡献 objective 改进 |

未来甚至可以做 **Search Attribution**：

```
Search Attribution
├── Operator Contribution
├── Move Contribution
└── Execution DAG Contribution
```

回答**为什么这个策略最好**，而不只是**哪个策略最好**。

### 4.5 Search Trace

完整的搜索日志（incumbent events、operator calls、acceptance decisions），支持 CP Profiler [5] 风格的可视化。

---

## 5. Composite Score (综合评分)

**仅基于前三层**（Outcome + Efficiency + Robustness）计算：

```
composite = 0.40×quality + 0.30×anytime + 0.15×efficiency + 0.15×stability
```

**权重说明**：

| 维度 | 权重 | 理由 |
|------|:----:|------|
| Quality (D1) | 40% | 最终解质量是核心目标 |
| Anytime (D2) | 30% | 工业场景常需任意时间切面都好 |
| Efficiency (D3) | 15% | 资源成本重要但次于质量 |
| Stability (D4) | 15% | 生产环境需要可靠性 |

若某维度数据不足（如 D4 要求 ≥5 seeds），其权重按比例分配给其余维度。

**Search Diagnostics (D5) 不参与总分**，单独展示。

---

## 6. 聚合层级

```
Level 1: Per-Run Evidence    — 单次运行的原始指标 + 评分
Level 2: Per-Instance Evidence — 同一 benchmark_id 多 seed 的统计
Level 3: Per-Group Score     — 一个 benchmark_group 下所有 instance 的均值
Level 4: Strategy Score      — 跨所有 group 的全局策略评分
```

每一级的维度分 = 下层维度分的算术平均。Stability (D4) 仅在 Level 2+ 有效。

---

## 7. 校准 (Calibration)

阈值设定遵循 **P75 校准原则** — 基于当前 benchmark suite 中真实运行数据的第 75 百分位：

```bash
python -m benchmarks.scoring --calibrate results/
```

输出各 group 的 P75 gap、P75 throughput、P75 CV，可用于更新硬编码值。

当前默认值基于：
- **gap_threshold**：工业 benchmark 标准（MIPLIB / TSPLIB 文献中的典型 gap 分布）
- **expected_throughput**：OptAgent release 构建的实测数据
- **cv_threshold**：工业求解器多次运行的典型变异范围

---

## 8. Raw Telemetry Schema

所有评估指标的数据来源：

| 层级 | 字段 | C++ 来源 | Python 字段名 |
|------|------|----------|---------------|
| **Telemetry** | incumbent trace | `SearchProgressLogger.incumbent_trace_` | `diagnostics["incumbent_trace_json"]` |
| | time to best | incumbent trace 最后一项 | `diagnostics["time_to_best_s"]` |
| | diversity | `TerminationTelemetry.diversity` | `diagnostics["diversity_at_termination"]` |
| | unimproved iterations | `TerminationTelemetry.unimproved_iterations` | `diagnostics["unimproved_iterations"]` |
| | total iterations | `SearchState.iterations` | `diagnostics["total_iterations"]` |
| | candidates evaluated | GA: `offspring_evaluated` / ALNS: `candidates_evaluated` | `diagnostics["ga_offspring_evaluated"]` |
| | termination reason | `TerminationDecision.reason` | `diagnostics["termination_reason"]` |
| | wall time | `SolveResult.wall_time_seconds` | `diagnostics["wall_time_seconds"]` |
| **Raw Metrics** | gap_rel | `(objective - reference) / |reference|` | 计算字段 |
| | primal_integral | `∫ gap(t) dt` | 从 incumbent trace 计算 |
| | throughput | `evaluations / wall_time` | 计算字段 |
| | cv | `std / |mean|` | 从多 seed 计算 |
| **Normalized Metrics** | quality_score | `f(gap_rel, gap_threshold)` | D1 |
| | anytime_score | `f(primal_integral, max_integral)` | D2 |
| | efficiency_score | `f(throughput, expected_throughput)` | D3 |
| | stability_score | `f(cv, worst_gap, feasibility)` | D4 |
| **Composite** | weighted average | `∑ weight_i × score_i` | 仅前三层 |

**设计原则**：Telemetry 和 Raw Metrics 永远不变，评分公式可以随经验调整。

---

## 9. 使用示例

```bash
# 运行 benchmark 并评估
python -m benchmarks.run --case tsplib_berlin52 --strategy ga --strategy advanced_ga \
  --time-limit-s 30 | python -m benchmarks.scoring --output scores.json

# 多 seed 运行后计算稳定性
for seed in $(seq 0 29); do
  python -m benchmarks.run --case tsplib_berlin52 --strategy ga --seed $seed
done | python -m benchmarks.scoring --output scores.json

# 查看校准建议
python -m benchmarks.scoring --calibrate results/
```

---

## 10. Phase 2 开发计划

| 优先级 | 功能 | 说明 | 预计工作量 |
|--------|------|------|-----------|
| **P0** | 统计显著性检验 | Wilcoxon / Friedman / Effect Size | 1 周 |
| **P0** | Time-to-Target | 固定目标达成时间/评估数 | 1 周 |
| **P1** | Operator Contribution | 算子级别贡献归因 | 2 周 |
| **P1** | ECDF Curves | COCO 风格的 ERT/ECDf 曲线 | 2 周 |
| **P2** | Search Trace Visualization | CP Profiler 风格的搜索树可视化 | 3 周 |
| **P2** | Anytime 扩展指标 | AUIC / Incumbent Curve / Time to X% | 1 周 |

---

## 参考文献

[1] Hansen, N., et al. (2021). *COCO: A Platform for Comparing Continuous Optimizers in a Black-Box Setting.* Optimization Methods and Software, 36(1), 114-144.

[2] Stuckey, P. J., et al. (2014). *The MiniZinc Challenge 2008–2013.* AI Magazine, 35(2), 55-60.

[3] Koch, T., et al. (2011). *MIPLIB 2010.* Mathematical Programming Computation, 3(2), 103-163.

[4] Achterberg, T. (2009). *SCIP: Solving Constraint Integer Programs.* Mathematical Programming Computation, 1(1), 1-41.

[5] Ohrimenko, O., et al. (2014). *Propagation via Lazy Clause Generation.* Constraints, 14(3), 357-391.

[6] Reinelt, G. (1991). *TSPLIB—A Traveling Salesman Problem Library.* ORSA Journal on Computing, 3(4), 376-384.

[7] Uchoa, E., et al. (2017). *New Benchmark Instances for the Capacitated Vehicle Routing Problem.* European Journal of Operational Research, 257(3), 845-858.

[8] Taillard, E. (1993). *Benchmarks for Basic Scheduling Problems.* European Journal of Operational Research, 64(2), 278-285.

[9] Burkard, R. E., et al. (1997). *QAPLIB–A Quadratic Assignment Problem Library.* Journal of Global Optimization, 10(4), 391-403.

[10] Berthold, T. (2013). *Measuring the Impact of Primal Heuristics.* Operations Research Letters, 41(6), 611-614.

[11] López-Ibáñez, M., et al. (2016). *The irace Package: Iterated Racing for Automatic Algorithm Configuration.* Operations Research Perspectives, 3, 43-58.

[12] Eiben, A. E., & Jelasity, M. (2002). *A Critical Note on Experimental Research Methodology in EC.* In CEC 2002, Vol. 1, pp. 582-587.

[13] Hoos, H. H., & Stützle, T. (2004). *Stochastic Local Search: Foundations and Applications.* Elsevier.

[14] Demšar, J. (2006). *Statistical Comparisons of Classifiers over Multiple Data Sets.* Journal of Machine Learning Research, 7, 1-30.

[15] Rankey, E., & Nelson, B. L. (2025). *Measuring the Effectiveness and Efficiency of Simulation Optimization Metaheuristic Algorithms.* Journal of Heuristics. https://doi.org/10.1007/s10732-025-09549-2

[16] Brockhoff, D., et al. (2022). *Anytime Performance Assessment in Blackbox Optimization Benchmarking.* ResearchGate. https://www.researchgate.net/publication/364046734
