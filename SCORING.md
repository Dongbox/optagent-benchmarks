# 策略评分框架 (Strategy Performance Scoring)

本文档说明 OptAgent 策略评分的设计动机、维度定义与计算规则。评分实现见 [`scoring.py`](scoring.py)。

---

## 为什么需要评分

Benchmark 原始结果（objective、runtime、feasibility）难以直接回答"这次策略改动有没有效"。工业界主流做法是构建量化评分体系：

| 求解器 | 评价方式 |
|--------|----------|
| Gurobi | incumbent evolution、primal/dual integral、node throughput |
| SCIP | per-heuristic calls/success/improvement/time |
| MiniZinc Challenge | Borda scoring + anytime penalty |
| MIPLIB | Primal integral (∫ gap(t) dt) |

OptAgent 采用类似思路，将搜索质量从多个维度量化为 0–100 分，再加权合成为综合分。

---

## 五个维度

| 维度 | 权重 | 评估内容 |
|------|:----:|----------|
| D1: Solution Quality | 35% | 最终解与参考解 (BKS) 的相对 gap |
| D2: Anytime Performance | 25% | 搜索全过程解质量积分 (Primal Integral) |
| D3: Runtime Efficiency | 15% | 搜索吞吐率 (evaluations/s) |
| D4: Stability | 15% | 多 seed 一致性 + 可行性率 + 最差情况控制 |
| D5: Search Dynamics | 10% | 多样性、停滞率、终止质量 |

综合分公式：

```
composite = 0.35×D1 + 0.25×D2 + 0.15×D3 + 0.15×D4 + 0.10×D5
```

若某维度数据不足（如 D4 要求 ≥5 seeds），其权重按比例分配给其余维度。

---

## D1: Solution Quality

衡量最终 objective 相对于参考解的差距。

```
gap_rel = (objective - reference_cost) / |reference_cost|

quality_score = max(0, 100 × (1 - gap_rel / gap_threshold))
```

- 达到或优于参考解 (gap ≤ 0) → 100 分
- gap 达到 threshold → 0 分
- 不可行解 → 固定 0 分

**gap_threshold** 按问题类型设定：

| 问题组 | gap_threshold | 含义 |
|--------|:-----:|------|
| routing (TSP/VRP) | 0.20 | 工业 TSP 中 20% gap 为中等表现 |
| scheduling | 0.50 | 调度问题通常难度更高 |
| assignment (QAP) | 0.30 | QAP 中等难度 |

**参考解来源**：优先使用 Best Known Solution (BKS)；未知时使用 suite 内最佳解（标记 `reference_type: "relative"`）。

---

## D2: Anytime Performance

衡量搜索**全过程**的解质量，而非仅看最终值。实际生产场景中，策略必须在任意时间切面都尽量好。

**Primal Integral 定义**：

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

- 早期即找到优良解并保持 → 高分
- 前期差、后期突然好 → 被惩罚（对比仅看最终 objective 的 D1）

**数据来源**：C++ kernel 的 `IncumbentEvent` 向量 — 每次 best 更新时记录 `(elapsed_seconds, objective)`。默认开启，通常 <50 事件/次运行，无性能开销。

---

## D3: Runtime Efficiency

衡量搜索吞吐量 — 单位时间内评估了多少候选解。

```
evaluations_per_s = total_candidates_evaluated / wall_time_seconds

throughput_score = min(100, 100 × log₁₀(evaluations_per_s) / log₁₀(expected_throughput))
```

使用对数尺度：从 1 eval/s 到 expected_throughput 线性映射到 0–100。

**expected_throughput** 基准（release 构建下的典型值）：

| 问题组 | 基准 (eval/s) | 依据 |
|--------|:-----:|------|
| routing | 100,000 | 中等规模 TSP/VRP |
| scheduling | 10,000 | 调度问题计算密集 |
| assignment | 50,000 | QAP 中等 |

**candidate 计数来源**：优先使用 `loop_candidates_evaluated`；若为 0 则 fallback 到 `ga_offspring_evaluated` (GA) 或 `alns_candidates_evaluated` (ALNS)。

---

## D4: Stability

衡量多次运行（不同 random seed）的结果一致性。最少需要 5 个 seed 才计算；发布级评分建议 ≥30 seeds。

```
stability_score = min(100, 0.5×consistency + 0.3×feasibility + 0.2×worst_case)
```

三个子指标：

**1. 解质量一致性 (CV-based)**：

```
cv = std(objectives) / |mean(objectives)|
consistency_score = max(0, 100 × (1 - cv / cv_threshold))
```

`cv_threshold` = 0.15 — 工业求解器的合理变异系数上界。

**2. 可行性率**：

```
feasibility_score = feasible_count / total_runs × 100
```

**3. 最差情况控制**：

```
worst_gap = (worst_objective - reference_cost) / |reference_cost|
worst_case_score = max(0, 100 × (1 - worst_gap / gap_threshold))
```

**输出统计量**：mean、median、std、best、worst、P5、P95。

---

## D5: Search Dynamics

评估搜索过程的"健康度"，仅依赖终止时快照字段。

```
dynamics_score = (diversity_score + stagnation_score + termination_quality) / 3
```

**1. Diversity 健康度**：

```
diversity_score = min(100, diversity_at_termination × 200)
```

diversity = 0 说明种群完全收敛（信息量丧失）；diversity = 0.5+ 为健康范围。

**2. Stagnation 控制**：

```
stagnation_ratio = unimproved_iterations / total_iterations
stagnation_score = max(0, 100 × (1 - stagnation_ratio / 0.8))
```

80% 以上迭代无改进 → 0 分。

**3. 终止质量**：

| termination_reason | 分数 |
|:---|:---:|
| `converged` / `optimal` | 100 |
| `diversity_exhausted` | 80 |
| `time_limit` | 60 |
| `iteration_limit` | 40 |
| `stagnation` | 20 |

---

## 聚合层级

```
Level 1: Per-Run Score       — 单次运行的 D1–D5 + composite
Level 2: Per-Instance Score  — 同一 benchmark_id 多 seed 的统计（含 D4 计算）
Level 3: Per-Group Score     — 一个 benchmark_group 下所有 instance 的均值
Level 4: Strategy Score      — 跨所有 group 的全局策略评分
```

每一级的维度分 = 下层维度分的算术平均。Stability (D4) 仅在 Level 2+ 有效。

---

## 校准

阈值的设定遵循 P75 校准原则 — 基于当前 benchmark suite 中真实运行数据的第 75 百分位：

```bash
python -m benchmarks.scoring --calibrate results/
```

输出各 group 的 P75 gap、P75 throughput、P75 CV，可用于更新硬编码值。

当前默认值基于：
- **gap_threshold**：工业 benchmark 标准（MIPLIB / TSPLIB 文献中的典型 gap 分布）
- **expected_throughput**：OptAgent release 构建的实测数据
- **cv_threshold**：工业求解器多次运行的典型变异范围

---

## 数据来源

评分所需字段及其采集路径：

| 字段 | C++ 来源 | Python 字段名 |
|------|----------|---------------|
| incumbent trace | `SearchProgressLogger.incumbent_trace_` | `diagnostics["incumbent_trace_json"]` |
| time to best | incumbent trace 最后一项 | `diagnostics["time_to_best_s"]` |
| diversity | `TerminationTelemetry.diversity` | `diagnostics["diversity_at_termination"]` |
| unimproved iterations | `TerminationTelemetry.unimproved_iterations` | `diagnostics["unimproved_iterations"]` |
| total iterations | `SearchState.iterations` | `diagnostics["total_iterations"]` |
| candidates evaluated | GA: `offspring_evaluated` / ALNS: `candidates_evaluated` | `diagnostics["ga_offspring_evaluated"]` |
| termination reason | `TerminationDecision.reason` | `diagnostics["termination_reason"]` |
| wall time | `SolveResult.wall_time_seconds` | `diagnostics["wall_time_seconds"]` |

所有字段在搜索完成后自动写入 `SolutionProto.diagnostics` (Struct)，通过 Python binding 的 `UnifiedSolution.diagnostics` dict 暴露。

---

## 使用示例

```bash
# 运行 benchmark 并评分
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

## Phase 2 预留

| 维度 | 说明 | 状态 |
|------|------|------|
| D6: Operator Score | 算子级别贡献归因（calls / accepted / improved / avg_delta） | 待 SearchMetrics 统一输出 |
| D3 阶段计时 | construct/search/evaluate/external 各阶段 wall_seconds | 待 C++ instrumentation |

---

## 参考

- [评分框架设计文档](../docs/plans/strategy-performance-scoring-2026-07-03.md)
- [MIPLIB Primal Integral](https://miplib.zib.de)
- [MiniZinc Challenge 评分规则](https://www.minizinc.org/challenge.html)
- [SCIP heuristic statistics](https://www.scipopt.org/)
