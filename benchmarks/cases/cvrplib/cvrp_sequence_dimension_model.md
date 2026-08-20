# CVRP：单主序列、depot 分隔符与容量维度建模

本文记录一种以单个 `sequence_var` 表示固定车队 CVRP 的建模方案。它把客户和 `K` 个 depot 副本放入同一个排列；每个 depot 副本代表同一物理仓库，但在排列中承担“下一条路线开始”的分隔符角色。

设客户数量为 `n`、车辆数为 `K`、车辆容量为 `Q`。主序列中的元素为：

```text
C1, C2, ..., Cn, D1, D2, ..., DK
```

主序列首项必须是某个 depot 节点，但不指定必须是哪一个 depot。一个可行排列例如：

```text
D1, C4, C1, D2, C3, C2, D3, C5
```

它代表的三条闭环路线为：

```text
D1 -> C4 -> C1 -> D2
D2 -> C3 -> C2 -> D3
D3 -> C5 -> D1
```

在距离图中，所有 `Dk` 都映射到同一个物理 depot 的距离；客户到 `Dk` 是回仓距离，`Dk` 到客户是出仓距离。

## 建模思路

| 步骤 | 建模内容 | OptAgent 接口及作用 |
| --- | --- | --- |
| 1 | 创建包含 `n` 个客户节点和 `K` 个 depot 节点的全排列 `master`。每个元素恰好出现一次。 | `ModelBuilder.sequence_var(size)`：创建待优化的节点排列。 |
| 2 | 通过虚拟起始类型 `START`，只允许 `START -> DEPOT`，从而强制 `master[0]` 是任意一个实际 depot 节点。`START` 不属于 `master`。 | `ModelBuilder.sequence_transition(..., start_type=START, valid=True)`：检查由虚拟初始类型到首项、以及相邻实际节点类型之间的转移是否合法；外层 `constraint(...)` 将其设为硬约束。 |
| 3 | 构造扩展距离矩阵。客户—客户使用原始距离，客户—depot / depot—客户使用物理仓库距离，depot—depot 使用有限的大惩罚 `M`。 | `ModelBuilder.sequence_transition_sum(...)`：后续按该矩阵计算路径总距离。 |
| 4 | 将客户需求作为贡献值、depot 贡献设为零；每遇到一个实际 depot 节点即重置负载。对每个客户限制其处理后的累计负载不超过 `Q`。由于所有需求非负，这等价于约束每个 depot 分段的路线负载不超过容量。 | `ModelBuilder.sequence_dimension(...)`：取得某客户处理后的、从最近 depot 开始累计的需求；`constraint(load <= Q)` 添加容量硬约束。 |
| 5 | 对 `master` 的相邻节点累加距离，并增加末项回到首项 depot 的回边。 | `ModelBuilder.sequence_transition_sum(..., include_return_edge=True)`：计算整个闭环的总路程。 |
| 6 | 最小化总距离。 | `ModelBuilder.minimize(...)`：添加最小化目标。 |

`sequence_dimension` 不认识虚拟 `START`，也不需要认识它。步骤 2 已经以硬约束保证 `master[0]` 是实际 depot，因此容量维度实际处理的是：

```text
某个 depot -> ... -> 其他 depot -> ... -> 序列尾部
```

最后一段从最后出现的 depot 累积至序列尾部；末项回到首项 depot 的距离边不增加任何客户需求，因此不需要让容量维度循环处理。

## 参考 `build_model` 代码

以下代码使用对称 CVRP 的标准输入：`customer_distances[i][j]` 是客户 `i` 到客户 `j` 的距离，`depot_distances[i]` 是物理 depot 与客户 `i` 的距离，`demands[i]` 是客户需求。为兼容 CP-SAT 的序列距离目标，距离和需求使用非负整数。

```python
from __future__ import annotations

from typing import Sequence

from optagent import ModelBuilder


def build_model(
    customer_distances: Sequence[Sequence[int]],
    depot_distances: Sequence[int],
    demands: Sequence[int],
    vehicle_capacity: int,
    vehicle_count: int,
) -> ModelBuilder:
    """Build a fixed-fleet symmetric CVRP model with one master sequence.

    `vehicle_count` is the number of depot separator nodes, not a collection
    of separately indexed vehicle variables.
    """

    customer_count = len(demands)
    if customer_count == 0:
        raise ValueError("CVRP requires at least one customer")
    if vehicle_count <= 0:
        raise ValueError("vehicle_count must be positive")
    if vehicle_count > customer_count:
        raise ValueError("this formulation requires vehicle_count <= customer_count")
    if vehicle_capacity < 0:
        raise ValueError("vehicle_capacity must be non-negative")
    if len(depot_distances) != customer_count:
        raise ValueError("depot_distances length must equal customer count")
    if len(customer_distances) != customer_count or any(
        len(row) != customer_count for row in customer_distances
    ):
        raise ValueError("customer_distances must be a square customer matrix")
    if any(demand < 0 for demand in demands):
        raise ValueError("CVRP demands must be non-negative")
    if any(demand > vehicle_capacity for demand in demands):
        raise ValueError("a customer demand exceeds vehicle capacity")

    # Local master IDs: customers 0..n-1; depots n..n+K-1.
    customers = tuple(range(customer_count))
    depot_ids = tuple(range(customer_count, customer_count + vehicle_count))
    initial_depot = depot_ids[0]  # 仅是默认排列首项，不是固定约束。
    master_size = customer_count + vehicle_count

    # Types are used only by sequence_transition's legality check.
    CUSTOMER_TYPE = 0
    DEPOT_TYPE = 1
    START_TYPE = 2       # virtual predecessor; not an element of master
    item_types = [CUSTOMER_TYPE] * customer_count + [DEPOT_TYPE] * vehicle_count

    # A valid non-empty segment must be depot -> customer -> ... -> depot.
    # START can reach only a depot, therefore master[0] is necessarily a depot.
    allowed_type_graph = {
        "size": 3,
        "edges": [
            {"from": START_TYPE, "to": DEPOT_TYPE, "cost": 0},
            {"from": DEPOT_TYPE, "to": CUSTOMER_TYPE, "cost": 0},
            {"from": CUSTOMER_TYPE, "to": CUSTOMER_TYPE, "cost": 0},
            {"from": CUSTOMER_TYPE, "to": DEPOT_TYPE, "cost": 0},
        ],
    }

    # M dominates every no-depot-to-depot Hamiltonian cycle: at most
    # `master_size` finite edges, each no larger than max_finite_edge.
    max_finite_edge = max(
        0,
        *depot_distances,
        *(cost for row in customer_distances for cost in row),
    )
    depot_to_depot_cost = master_size * max(1, max_finite_edge) + 1

    # Expand the physical CVRP distance matrix to K copies of its depot.
    distance_graph = [[0] * master_size for _ in range(master_size)]
    for left in range(master_size):
        for right in range(master_size):
            if left == right:
                continue
            left_is_customer = left in customers
            right_is_customer = right in customers
            if left_is_customer and right_is_customer:
                distance_graph[left][right] = customer_distances[left][right]
            elif left_is_customer:  # customer -> a depot copy
                distance_graph[left][right] = depot_distances[left]
            elif right_is_customer:  # a depot copy -> customer
                distance_graph[left][right] = depot_distances[right]
            else:  # two distinct depot copies: empty route / idle vehicle penalty
                distance_graph[left][right] = depot_to_depot_cost

    builder = ModelBuilder(
        metadata={
            "problem_type": "CVRP",
            "model_style": "master_sequence_depot_resets",
            "objective_sense": "minimize",
        }
    )
    master = builder.sequence_var(
        master_size,
        default=[initial_depot, *customers, *depot_ids[1:]],
        name="master",
    )

    builder.constraint(
        builder.sequence_transition(
            master,
            allowed_type_graph,
            item_types=item_types,
            start_type=START_TYPE,
            valid=True,
            sparse_edge_semantics="forbidden",
            name="start_at_depot_and_no_linear_empty_route",
        ),
        name="start_at_depot_and_no_linear_empty_route",
    )

    # Depot nodes contribute zero; customer i contributes demands[i].
    contributions = [*demands, *([0] * vehicle_count)]
    for customer in customers:
        load_after_customer = builder.sequence_dimension(
            master,
            initial_value=0,
            contributions=contributions,
            item_types=item_types,
            reset_item_ids=list(depot_ids),
            reset_type_edges=[],
            query_item_id=customer,
            query="after",
            lower_bound=0,
            upper_bound=vehicle_capacity,
            name=f"route_load_after_customer_{customer}",
        )
        # The explicit constraint is retained even though the bounds are also
        # recorded in the dimension payload.
        builder.constraint(
            load_after_customer <= vehicle_capacity,
            name=f"capacity_after_customer_{customer}",
        )

    total_distance = builder.sequence_transition_sum(
        master,
        distance_graph,
        include_return_edge=True,
        cost_semantics="distance",
    )
    builder.minimize(total_distance, name="total_distance")
    return builder
```

## 备注

- 两个 depot 节点之间的距离设为 `0`，可使连续 depot 表示空路线：在本模型中等价于车辆数只作为“至多 `K` 辆”的上限，而非要求 `K` 辆车都工作；并不表示可使用超过 `K` 辆车。
- 两个 depot 节点之间的距离设为 `inf`，语义上相当于不允许车辆空闲。实际 OptAgent 图和 MILP/CP-SAT 后端应使用有限整数 `M`，不应传入 Python 的 `math.inf`。代码中的 `M` 大于任何不含 depot—depot 边的完整闭环距离，因此只要存在这种可行解，最优解不会选择 depot—depot 边。
- `sequence_transition(..., valid=True)` 检查线性相邻转移和虚拟 `START -> master[0]`，不检查末项回到首项的回边。末项 depot 到首项 depot 的情况由 `sequence_transition_sum(include_return_edge=True)` 中的 `M` 惩罚处理。
- 该文档描述的是模型语义与 Builder 接口。只能使用 `solve()`。