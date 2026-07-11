from __future__ import annotations

from optagent import SolutionStatus, UnifiedSolution

from benchmarks.cases.miplib2017.linear_mip._domain import (
    MipCase,
    MpsLinearConstraint,
    MpsVariableSpec,
    ParsedMpsInstance,
)


def test_mip_solution_metrics_use_public_diagnostics() -> None:
    case = MipCase(
        benchmark_id="miplib2017_test",
        family="exact_linear_mip",
        size={"variables": 2, "constraints": 1},
        data={},
        reference={"objective": 1.0},
        problem_description="test MIP",
    )
    case._set_build_context(
        {
            "instance": ParsedMpsInstance(
                name="test",
                objective_row="cost",
                objective_sense="min",
                objective_terms=(("x", 1.0),),
                constraints=(MpsLinearConstraint("limit", "L", (("x", 1.0),), 1.0),),
                variables={
                    "x": MpsVariableSpec("x", is_binary=True),
                    "y": MpsVariableSpec("y", lb=0.0, ub=2.0),
                },
            )
        }
    )
    solution = UnifiedSolution(
        solver_name="optx",
        status=SolutionStatus.OPTIMAL,
        variable_values={1: True, 2: 0.0},
        objective_values={3: 1.0},
        constraint_values={4: True},
        feasible=True,
        dag_recheck_passed=True,
        diagnostics={
            "backend": "optx",
            "mip_gap": 0.0,
            "constraint_violation_policy": "native_validation",
        },
    )

    metrics = case.solution_metrics(solution)

    assert metrics["objective"] == 1.0
    assert metrics["metadata"]["backend"] == "optx"
    assert metrics["metadata"]["mip_gap"] == 0.0
    assert metrics["metadata"]["constraint_violation_policy"] == "native_validation"
    assert metrics["metadata"]["variables"] == 2
    assert metrics["metadata"]["constraints"] == 1
