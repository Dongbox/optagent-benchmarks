from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from optagent import ModelBuilder

from benchmarks.loaders.exact_linear_mip import MpsLinearConstraint, ParsedMpsInstance


@dataclass(frozen=True)
class MipBenchmarkModel:
    program: Any
    variable_node_ids: dict[str, int]
    instance: ParsedMpsInstance


def build_mip_model(case: dict[str, Any], instance: ParsedMpsInstance) -> MipBenchmarkModel:
    builder = ModelBuilder(
        metadata={
            "benchmark_id": case["benchmark_id"],
            "family": "exact_linear_mip",
            "model_style": "mps_linear_mp",
            "source": "MIPLIB 2017",
            "variables": instance.variable_count,
            "constraints": instance.constraint_count,
            "nonzeros": instance.nonzero_count,
        }
    )
    const_cache: dict[float, Any] = {}
    variable_exprs: dict[str, Any] = {}

    def const_expr(value: float) -> Any:
        normalized = float(value)
        expr = const_cache.get(normalized)
        if expr is None:
            expr = builder.const(normalized)
            const_cache[normalized] = expr
        return expr

    for name, spec in instance.variables.items():
        if spec.is_binary:
            expr = builder.bool_var(default=False, name=name)
        elif spec.is_integer:
            lb = _coerce_int_bound(spec.lb)
            ub = _coerce_int_bound(spec.ub)
            expr = builder.int_var(default=_default_for_integer(lb, ub), lb=lb, ub=ub, name=name)
        else:
            lb = None if spec.lb is None else float(spec.lb)
            ub = None if spec.ub is None else float(spec.ub)
            expr = builder.float_var(default=_default_for_float(lb, ub), lb=lb, ub=ub, name=name)
        variable_exprs[name] = expr

    objective_expr = _weighted_sum(builder, const_expr, variable_exprs, instance.objective_terms)
    if instance.objective_sense == "max":
        builder.maximize(objective_expr, name=instance.objective_row)
    else:
        builder.minimize(objective_expr, name=instance.objective_row)

    for row in instance.constraints:
        _add_constraint(builder, const_expr, variable_exprs, row)

    return MipBenchmarkModel(
        program=builder.freeze(),
        variable_node_ids={name: expr.node_id for name, expr in variable_exprs.items()},
        instance=instance,
    )


def _add_constraint(
    builder: ModelBuilder,
    const_expr: Any,
    variable_exprs: dict[str, Any],
    row: MpsLinearConstraint,
) -> None:
    lhs = _weighted_sum(builder, const_expr, variable_exprs, row.terms)
    rhs = const_expr(row.rhs)
    if row.range_value is None:
        if row.sense == "L":
            builder.constraint(lhs <= rhs, name=row.name)
            return
        if row.sense == "G":
            builder.constraint(lhs >= rhs, name=row.name)
            return
        if row.sense == "E":
            builder.constraint(lhs == rhs, name=row.name)
            return
    lb, ub = _range_bounds(row)
    if lb is not None:
        builder.constraint(lhs >= const_expr(lb), name=f"{row.name}_range_lb")
    if ub is not None:
        builder.constraint(lhs <= const_expr(ub), name=f"{row.name}_range_ub")


def _range_bounds(row: MpsLinearConstraint) -> tuple[float | None, float | None]:
    if row.range_value is None:
        raise ValueError("range_value is required")
    rhs = float(row.rhs)
    span = abs(float(row.range_value))
    if row.sense == "L":
        return rhs - span, rhs
    if row.sense == "G":
        return rhs, rhs + span
    if row.sense == "E":
        if row.range_value >= 0:
            return rhs, rhs + span
        return rhs - span, rhs
    raise ValueError(f"unsupported row sense: {row.sense}")


def _weighted_sum(
    builder: ModelBuilder,
    const_expr: Any,
    variables: dict[str, Any],
    terms: tuple[tuple[str, float], ...],
) -> Any:
    if not terms:
        return const_expr(0.0)
    exprs: list[Any] = []
    for variable_name, coefficient in terms:
        variable = variables[variable_name]
        if coefficient == 1:
            exprs.append(variable)
        elif coefficient == -1:
            exprs.append(-variable)
        else:
            exprs.append(variable * const_expr(coefficient))
    if len(exprs) == 1:
        return exprs[0]
    return builder.sum(*exprs)


def _coerce_int_bound(value: float | None) -> int | None:
    if value is None:
        return None
    rounded = int(round(value))
    if abs(float(value) - rounded) > 1e-9:
        raise ValueError(f"expected integer bound, got {value}")
    return rounded


def _default_for_integer(lb: int | None, ub: int | None) -> int:
    if lb is not None and ub is not None and lb == ub:
        return lb
    if lb is not None and lb > 0:
        return lb
    if ub is not None and ub < 0:
        return ub
    return 0


def _default_for_float(lb: float | None, ub: float | None) -> float:
    if lb is not None and ub is not None and abs(lb - ub) <= 1e-12:
        return lb
    if lb is not None and lb > 0.0:
        return lb
    if ub is not None and ub < 0.0:
        return ub
    return 0.0
