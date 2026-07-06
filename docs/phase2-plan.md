# Strategy Performance Evaluation — Phase 2 开发计划

基于专家评审反馈，本文档详细说明 Phase 2 扩展功能的需求、设计与实现计划。

---

## 总体目标

从**评分系统**升级为**评估平台**：

```
当前状态 (Phase 1)
Raw Metrics → Score

目标状态 (Phase 2)
Raw Telemetry → Evidence Chain → Score (optional)
                     ↓
              Search Attribution
```

核心原则：**原始数据永远不变，评分公式可以演进**。

---

## P0: 统计显著性检验

### 需求背景

工业论文标配 [Demšar 2006]：任何性能提升都必须回答"是否统计显著"。

当前问题：
- GA 提升 0.8% → 用户质疑："是不是随机？"
- 只能靠人工判断 CV 是否合理

### 功能设计

#### 1. Pairwise Comparison (Wilcoxon Signed-Rank)

**输入**：两策略在同一组 benchmark instances 上的多次运行结果

**输出**：

```json
{
  "comparison": {
    "strategy_a": "ga",
    "strategy_b": "advanced_ga",
    "test": "wilcoxon",
    "statistic": 234.5,
    "p_value": 0.0023,
    "significant": true,
    "alpha": 0.05,
    "effect_size": 0.42,
    "interpretation": "medium effect"
  }
}
```

**实现**：

```python
from scipy.stats import wilcoxon

def pairwise_comparison(scores_a: list[float], scores_b: list[float]) -> dict:
    """
    Wilcoxon signed-rank test for paired samples.
    
    Args:
        scores_a, scores_b: Matched objective values on same instances
    
    Returns:
        {statistic, p_value, significant, effect_size}
    """
    statistic, p_value = wilcoxon(scores_a, scores_b)
    
    # Cohen's d for effect size
    diff = [a - b for a, b in zip(scores_a, scores_b)]
    mean_diff = mean(diff)
    pooled_std = sqrt((std(scores_a)**2 + std(scores_b)**2) / 2)
    effect_size = mean_diff / pooled_std if pooled_std > 0 else 0
    
    interpretation = interpret_effect_size(abs(effect_size))
    
    return {
        "test": "wilcoxon",
        "statistic": float(statistic),
        "p_value": float(p_value),
        "significant": p_value < 0.05,
        "effect_size": effect_size,
        "interpretation": interpretation,
    }

def interpret_effect_size(d: float) -> str:
    """Cohen's d interpretation."""
    if d < 0.2:
        return "negligible"
    elif d < 0.5:
        return "small"
    elif d < 0.8:
        return "medium"
    else:
        return "large"
```

#### 2. Multi-Strategy Comparison (Friedman Test)

**输入**：多策略在同一组 instances 上的结果矩阵

**输出**：

```json
{
  "comparison": {
    "strategies": ["ga", "advanced_ga", "alns"],
    "test": "friedman",
    "statistic": 18.4,
    "p_value": 0.0001,
    "significant": true,
    "post_hoc": [
      {"pair": ["ga", "advanced_ga"], "p_value": 0.12, "significant": false},
      {"pair": ["ga", "alns"], "p_value": 0.003, "significant": true},
      {"pair": ["advanced_ga", "alns"], "p_value": 0.021, "significant": true}
    ]
  }
}
```

**实现**：

```python
from scipy.stats import friedmanchisquare
from scikit_posthocs import posthoc_nemenyi_friedman

def multi_strategy_comparison(
    results: dict[str, list[float]]  # strategy -> scores
) -> dict:
    """
    Friedman test + Nemenyi post-hoc.
    
    Args:
        results: {strategy_name: [score_1, score_2, ...]}
                 All lists must have same length (same instances)
    
    Returns:
        {test, statistic, p_value, post_hoc}
    """
    strategies = list(results.keys())
    scores = [results[s] for s in strategies]
    
    statistic, p_value = friedmanchisquare(*scores)
    
    # Post-hoc if significant
    post_hoc = []
    if p_value < 0.05:
        # Build dataframe for posthoc test
        import pandas as pd
        df = pd.DataFrame(results)
        ph_matrix = posthoc_nemenyi_friedman(df)
        
        for i, s1 in enumerate(strategies):
            for j, s2 in enumerate(strategies):
                if i < j:
                    post_hoc.append({
                        "pair": [s1, s2],
                        "p_value": float(ph_matrix.loc[s1, s2]),
                        "significant": ph_matrix.loc[s1, s2] < 0.05,
                    })
    
    return {
        "test": "friedman",
        "strategies": strategies,
        "statistic": float(statistic),
        "p_value": float(p_value),
        "significant": p_value < 0.05,
        "post_hoc": post_hoc,
    }
```

#### 3. CLI 集成

```bash
# Pairwise
python -m benchmarks.scoring --compare \
  --baseline results/ga.json \
  --candidate results/advanced_ga.json \
  --output comparison.json

# Multi-strategy
python -m benchmarks.scoring --compare-all \
  --input-dir results/ \
  --output friedman.json
```

#### 4. Dashboard 展示

在 Strategy Comparison 页面增加 Statistical Significance 卡片：

```
┌─ Statistical Significance ──────────────────┐
│ GA vs Advanced GA                           │
│ Wilcoxon p = 0.0023 ✓ significant          │
│ Effect size d = 0.42 (medium)              │
│                                             │
│ Overall Friedman χ² = 18.4, p < 0.0001     │
│ Post-hoc (Nemenyi):                         │
│   GA ≈ Advanced GA     (p = 0.12)          │
│   GA < ALNS            (p = 0.003) ✓       │
│   Advanced GA < ALNS   (p = 0.021) ✓       │
└─────────────────────────────────────────────┘
```

### 工作量估算

- **scoring.py 扩展**：2 天
- **CLI 参数**：0.5 天
- **Dashboard UI**：2 天
- **文档 + 测试**：1.5 天

**总计**：1 周

---

## P0: Time-to-Target (参考 COCO)

### 需求背景

COCO benchmark [Hansen 2021] 的核心指标：**达到固定目标所需的资源**。

当前问题：
- Throughput (eval/s) 无法跨算法公平比较（不同 evaluation 成本差异巨大）
- 只看最终 objective 无法评估"快速达到可用解"的能力

### 功能设计

#### 1. 固定目标定义

常见目标设定：

| 目标类型 | 定义 | 工业应用 |
|---------|------|----------|
| **Absolute** | objective ≤ target_value | 已知 BKS 或合同要求 |
| **Relative** | gap ≤ X% | 工业界常用（如 5% gap） |
| **Percentile** | 达到历史 P95 水平 | 内部 baseline 比较 |

#### 2. 指标定义

```python
@dataclass
class TimeToTargetMetrics:
    target_gap: float  # 目标 gap（如 0.05 表示 5%）
    
    # 达到目标的时间/评估数（未达到则为 None）
    time_to_target: float | None
    evaluations_to_target: int | None
    
    # 固定预算下的目标达成率
    target_reached_in_budget: bool
    
    # COCO ERT (Expected Running Time)
    ert: float  # 达到目标所需的期望时间（多 seed 平均）
    success_rate: float  # 多 seed 中达到目标的比例
```

#### 3. 计算逻辑

```python
def compute_time_to_target(
    incumbent_trace: list[IncumbentEvent],
    reference_cost: float,
    target_gap: float,
    time_budget: float,
) -> TimeToTargetMetrics:
    """
    计算达到目标所需的时间和评估数。
    
    Args:
        incumbent_trace: [(elapsed_s, objective), ...]
        reference_cost: 参考解（BKS）
        target_gap: 目标 gap（如 0.05 表示 5%）
        time_budget: 总时间预算
    
    Returns:
        TimeToTargetMetrics
    """
    target_obj = reference_cost * (1 + target_gap)
    
    # 找到第一个达到目标的事件
    for event in incumbent_trace:
        if event.objective <= target_obj:
            return TimeToTargetMetrics(
                target_gap=target_gap,
                time_to_target=event.elapsed_s,
                evaluations_to_target=event.evaluations,  # Phase 2 需要在 trace 中记录
                target_reached_in_budget=True,
                ert=event.elapsed_s,
                success_rate=1.0,
            )
    
    # 未达到目标
    return TimeToTargetMetrics(
        target_gap=target_gap,
        time_to_target=None,
        evaluations_to_target=None,
        target_reached_in_budget=False,
        ert=float('inf'),
        success_rate=0.0,
    )

def aggregate_time_to_target(
    runs: list[TimeToTargetMetrics],
) -> TimeToTargetMetrics:
    """
    多 seed 聚合（COCO ERT 计算）。
    """
    success_runs = [r for r in runs if r.target_reached_in_budget]
    success_rate = len(success_runs) / len(runs)
    
    if success_rate > 0:
        avg_time = sum(r.time_to_target for r in success_runs) / len(success_runs)
        # COCO ERT: 考虑失败的 runs
        ert = avg_time / success_rate
    else:
        avg_time = None
        ert = float('inf')
    
    return TimeToTargetMetrics(
        target_gap=runs[0].target_gap,
        time_to_target=avg_time,
        evaluations_to_target=None,  # 需要聚合
        target_reached_in_budget=success_rate > 0,
        ert=ert,
        success_rate=success_rate,
    )
```

#### 4. 多目标评估（ECDF Curve）

COCO 风格的 ECDF (Empirical Cumulative Distribution Function)：

```python
def compute_ecdf_curve(
    runs: list[list[IncumbentEvent]],
    reference_cost: float,
    target_gaps: list[float] = [0.01, 0.05, 0.10, 0.20],
) -> dict:
    """
    计算 ECDF 曲线：不同时间下达到各目标的成功率。
    
    Returns:
        {
            "target_gaps": [0.01, 0.05, 0.10, 0.20],
            "time_points": [0.1, 0.5, 1.0, 5.0, 10.0, ...],
            "ecdf": [[success_rate_at_t1, ...], ...]  # shape: (len(target_gaps), len(time_points))
        }
    """
    pass  # 实现略
```

#### 5. C++ Kernel 扩展

在 `IncumbentEvent` 中增加 `evaluations` 字段：

```cpp
struct IncumbentEvent {
  double elapsed_seconds;
  double objective;
  int64_t evaluations;  // 新增：累计评估数
};
```

#### 6. Dashboard 展示

在 Run Detail 页面增加 Time-to-Target 卡片：

```
┌─ Time to Target ────────────────────────────┐
│ Target: 5% gap (obj ≤ 7692)                 │
│ Time to target: 2.3s (23% of budget)        │
│ Evaluations to target: 23,451               │
│                                             │
│ Multi-seed (30 runs):                       │
│   Success rate: 93.3%                       │
│   ERT: 2.8s ± 0.6s                          │
│   Evaluations: 28,123 ± 5,432               │
│                                             │
│ ECDF Curve:                                 │
│   [Chart: success_rate(t) for multiple targets]
└─────────────────────────────────────────────┘
```

### 工作量估算

- **C++ kernel 扩展**（IncumbentEvent + evaluations）：1 天
- **scoring.py TTT 计算**：2 天
- **ECDF curve**：1.5 天
- **Dashboard UI**：2 天
- **文档 + 测试**：1.5 天

**总计**：1 周

---

## P1: Operator Contribution

### 需求背景

这是 **OptAgent 最大优势**：透明化算子贡献，对标 SCIP heuristic statistics [Achterberg 2009]。

当前问题：
- 不知道哪个 destroy/repair/mutation 真正有效
- 调参时只能靠猜测

### 功能设计

#### 1. Telemetry Schema

在 `SolutionProto.diagnostics` 中增加 `operator_stats_json`：

```json
{
  "operator_stats": [
    {
      "operator_name": "random_removal",
      "operator_type": "destroy",
      "calls": 1234,
      "accepted": 567,
      "improved": 123,
      "total_delta": -456.7,
      "avg_delta": -3.7,
      "cumulative_contribution": -456.7,
      "avg_time_ms": 0.42
    },
    {
      "operator_name": "greedy_repair",
      "operator_type": "repair",
      "calls": 1234,
      "accepted": 890,
      "improved": 234,
      "total_delta": -1234.5,
      "avg_delta": -5.3,
      "cumulative_contribution": -1234.5,
      "avg_time_ms": 1.2
    }
  ]
}
```

#### 2. C++ Kernel 采集

在 `SearchState` 中增加 `OperatorStats`：

```cpp
struct OperatorStats {
  std::string name;
  std::string type;  // "destroy" | "repair" | "mutation" | "crossover" | "select"
  
  int64_t calls = 0;
  int64_t accepted = 0;
  int64_t improved = 0;
  
  double total_delta = 0.0;
  double cumulative_contribution = 0.0;
  
  double total_time_seconds = 0.0;
};

class SearchState {
  // ...
  std::unordered_map<std::string, OperatorStats> operator_stats_;
  
  void RecordOperatorCall(
      const std::string& operator_name,
      bool accepted,
      double delta,
      double elapsed_seconds
  );
};
```

#### 3. Evaluation 指标

```python
@dataclass
class OperatorContribution:
    operator_name: str
    operator_type: str
    
    calls: int
    acceptance_rate: float  # accepted / calls
    improvement_rate: float  # improved / calls
    
    avg_delta: float
    cumulative_contribution: float
    contribution_percentage: float  # 占总改进的百分比
    
    avg_time_ms: float
    efficiency: float  # |avg_delta| / avg_time_ms

def rank_operators(
    operator_stats: list[OperatorContribution],
) -> list[OperatorContribution]:
    """
    按 cumulative_contribution 降序排序。
    """
    return sorted(operator_stats, key=lambda x: x.cumulative_contribution, reverse=True)
```

#### 4. Dashboard 展示

在 Run Detail 页面增加 Operator Contribution 卡片：

```
┌─ Operator Contribution ─────────────────────┐
│ Top Contributors (by cumulative improvement)│
│                                             │
│ 1. greedy_repair                            │
│    Contribution: -1234.5 (45.2%)            │
│    Calls: 1234, Accepted: 72%, Improved: 19%│
│    Avg Δ: -5.3, Efficiency: -4.4/ms         │
│                                             │
│ 2. random_removal + regret_repair           │
│    Contribution: -890.2 (32.6%)             │
│    ...                                      │
│                                             │
│ [Full table with sort/filter options]       │
└─────────────────────────────────────────────┘
```

#### 5. 策略级聚合

跨多个 runs 聚合算子统计，回答"这个策略为什么好"：

```
┌─ Strategy Attribution: advanced_ga ─────────┐
│ Average Operator Contribution (30 runs)     │
│                                             │
│ Destroy operators:                          │
│   worst_removal       35.2% ± 8.4%          │
│   random_removal      28.1% ± 12.3%         │
│   shaw_removal        15.7% ± 6.2%          │
│                                             │
│ Repair operators:                           │
│   greedy_repair       52.3% ± 9.1%          │
│   regret_repair       31.4% ± 7.8%          │
│                                             │
│ Key insight: worst_removal + greedy_repair  │
│              is the most effective combo    │
└─────────────────────────────────────────────┘
```

### 工作量估算

- **C++ kernel OperatorStats**：2 天
- **SearchState 集成**（各 operator 调用处插桩）：2 天
- **scoring.py operator 分析**：1.5 天
- **Dashboard UI**：2.5 天
- **文档 + 测试**：2 天

**总计**：2 周

---

## P1: ECDF Curves (COCO 风格)

### 需求背景

COCO benchmark 核心可视化：不同时间预算下的目标达成率。

### 功能设计

见 P0 Time-to-Target 中的 `compute_ecdf_curve`。

Dashboard 展示：

```
┌─ ECDF: Success Rate over Time ─────────────┐
│                                             │
│ 1.0 ┤                           ╭─────────  │
│     │                      ╭────╯           │
│ 0.8 ┤                 ╭────╯                │
│     │            ╭────╯                     │
│ 0.6 ┤       ╭────╯                          │
│     │  ╭────╯                               │
│ 0.4 ┤──╯                                    │
│     │                                       │
│ 0.2 ┤                                       │
│     │                                       │
│ 0.0 ┼───────────────────────────────────── │
│     0s    5s    10s   15s   20s   25s   30s│
│                                             │
│ Legend:                                     │
│   ─ 1% gap  ─ 5% gap  ─ 10% gap  ─ 20% gap │
└─────────────────────────────────────────────┘
```

### 工作量估算

- **ECDF 计算**（已包含在 TTT 中）：0.5 天
- **Dashboard 图表**：1.5 天

**总计**：2 天（合并到 P0 TTT 工作包）

---

## P2: Search Trace Visualization

### 需求背景

CP Profiler [Ohrimenko 2014] 风格的搜索树可视化，用于深度调试。

### 功能设计

#### 1. Trace Schema

```json
{
  "search_trace": [
    {
      "timestamp_s": 0.123,
      "event_type": "operator_call",
      "operator_name": "random_removal",
      "solution_id": 42,
      "objective_before": 1234.5,
      "objective_after": 1198.3,
      "delta": -36.2,
      "accepted": true
    },
    {
      "timestamp_s": 0.125,
      "event_type": "incumbent_update",
      "solution_id": 42,
      "objective": 1198.3
    },
    {
      "timestamp_s": 0.130,
      "event_type": "restart",
      "reason": "diversity_exhausted"
    }
  ]
}
```

#### 2. Visualization

使用 D3.js 或 Plotly 绘制交互式时间轴：

```
Time ──────────────────────────────────────────→
     │
0.0s ●────────────────────────────────────────
     │  construct: greedy (obj=1500)
     │
0.5s     ●─────────────────────────────────────
     │   mutation: swap (obj=1450, accepted)
     │
1.0s         ●────×────────────────────────────
     │       │    │
     │    improved rejected
     │
2.0s                 ⟲ restart
     │
...
```

#### 3. 过滤和聚合

- 按 operator_type 过滤
- 只显示 improved events
- 按时间窗口聚合

### 工作量估算

- **C++ trace 采集**：2 天
- **JSON schema 设计**：0.5 天
- **Dashboard D3.js 可视化**：3 天
- **交互功能（过滤/缩放/高亮）**：2 天

**总计**：3 周（优先级 P2，可推迟）

---

## P2: Anytime 扩展指标

### 需求背景

Primal Integral 是标准指标，但可以扩展更多 anytime 视角。

### 功能设计

#### 1. Area Under Improvement Curve (AUIC)

```python
def compute_auic(incumbent_trace: list[IncumbentEvent]) -> float:
    """
    计算改进幅度积分（而非 gap 积分）。
    
    AUIC = ∫ improvement_rate(t) dt
    """
    if not incumbent_trace:
        return 0.0
    
    initial_obj = incumbent_trace[0].objective
    auic = 0.0
    
    for i in range(1, len(incumbent_trace)):
        dt = incumbent_trace[i].elapsed_s - incumbent_trace[i-1].elapsed_s
        improvement_rate = (initial_obj - incumbent_trace[i].objective) / initial_obj
        auic += improvement_rate * dt
    
    return auic
```

#### 2. Time to X% of Best

```python
def time_to_percentage(
    incumbent_trace: list[IncumbentEvent],
    final_best: float,
    percentage: float = 0.95,
) -> float | None:
    """
    达到最优解 X% 的时间。
    
    例如：percentage=0.95 表示达到 95% 质量的时间。
    """
    target_obj = final_best / percentage
    
    for event in incumbent_trace:
        if event.objective <= target_obj:
            return event.elapsed_s
    
    return None
```

### 工作量估算

- **scoring.py 扩展**：1 天
- **Dashboard 展示**：1 天

**总计**：1 周（低优先级）

---

## 总工作量估算

| 优先级 | 功能 | 工作量 | 依赖 |
|--------|------|--------|------|
| **P0** | 统计显著性检验 | 1 周 | 无 |
| **P0** | Time-to-Target | 1 周 | C++ IncumbentEvent 扩展 |
| **P1** | Operator Contribution | 2 周 | C++ SearchState 扩展 |
| **P1** | ECDF Curves | （已包含在 TTT 中） | P0 TTT |
| **P2** | Search Trace Visualization | 3 周 | C++ trace 采集 |
| **P2** | Anytime 扩展指标 | 1 周 | 无 |

**P0 总计**：2 周（可并行开发）  
**P0+P1 总计**：4 周  
**全部完成**：8 周

---

## 开发顺序建议

### Sprint 1 (Week 1-2): P0 基础设施

1. **统计显著性检验**（Week 1）
   - Day 1-2: scipy.stats 集成 + scoring.py
   - Day 3-4: Dashboard UI
   - Day 5: 文档 + 测试

2. **Time-to-Target**（Week 2）
   - Day 1: C++ IncumbentEvent 扩展
   - Day 2-3: scoring.py TTT 计算 + ECDF
   - Day 4-5: Dashboard UI
   - Day 6: 文档 + 测试

### Sprint 2 (Week 3-4): P1 高级功能

3. **Operator Contribution**（Week 3-4）
   - Day 1-2: C++ OperatorStats 结构
   - Day 3-4: SearchState 集成（GA/ALNS 插桩）
   - Day 5-6: scoring.py operator 分析
   - Day 7-9: Dashboard UI
   - Day 10: 文档 + 测试

### Sprint 3 (Week 5-8): P2 可选功能

4. **Search Trace Visualization**（Week 5-7）
5. **Anytime 扩展指标**（Week 8）

---

## 验收标准

### P0

- [ ] Wilcoxon / Friedman 检验可通过 CLI 调用
- [ ] Dashboard 显示 p-value + effect size
- [ ] Time-to-Target 可在 Run Detail 查看
- [ ] ECDF 曲线可展示多目标达成率
- [ ] 所有 P0 功能有单元测试（覆盖率 ≥80%）

### P1

- [ ] Operator Contribution 在 Dashboard 可查看 Top 10
- [ ] 策略级聚合显示平均算子贡献
- [ ] 文档说明如何解读算子统计

### P2

- [ ] Search Trace 可在 Dashboard 交互式展示
- [ ] 支持按时间/operator/event_type 过滤
- [ ] AUIC / Time-to-X% 可在 Anytime 卡片查看

---

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| C++ kernel 改动影响性能 | 高 | 使用条件编译（debug only），release 构建关闭 trace |
| Operator 插桩成本高 | 中 | 只记录摘要统计，不记录完整 trace |
| Dashboard 数据量过大 | 中 | 前端分页 + 后端聚合，不传输原始 trace |
| 统计检验误用 | 低 | 文档说明适用场景 + 假设检验前提 |

---

## 后续演进方向

Phase 3（6个月+）：

- **Search Attribution**：基于 Shapley Value 的算子贡献归因
- **Adaptive Benchmark**：根据历史表现自动调整 instance 难度
- **Multi-Objective Evaluation**：Pareto front + hypervolume
- **Explainable Search**：自然语言解释"为什么这次搜索失败"

---

## 参考文献

见 EVALUATION.md 参考文献部分。
