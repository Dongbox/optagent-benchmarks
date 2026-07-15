from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

from benchmarks.cases.base import BenchmarkCase, SolutionVerification
from benchmarks.run import LocalRunBudget, _verify_observation_snapshots, run_benchmark_case


@dataclass(frozen=True)
class _FakeSolution:
    solver_name: str = "fake"
    status: str = "feasible"
    feasible: bool = True
    variable_values: dict[int, Any] = None  # type: ignore[assignment]
    objective_values: dict[int, Any] = None  # type: ignore[assignment]
    constraint_values: dict[int, Any] = None  # type: ignore[assignment]
    metadata: dict[str, Any] = None  # type: ignore[assignment]
    diagnostics: dict[str, Any] = None  # type: ignore[assignment]
    observations: tuple[Any, ...] = ()
    solution_snapshots: dict[str, Any] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        object.__setattr__(self, "variable_values", self.variable_values or {})
        object.__setattr__(self, "objective_values", self.objective_values or {1: 1.0})
        object.__setattr__(self, "constraint_values", self.constraint_values or {})
        object.__setattr__(self, "metadata", self.metadata or {})
        object.__setattr__(self, "diagnostics", self.diagnostics or {})
        object.__setattr__(self, "solution_snapshots", self.solution_snapshots or {})

    @property
    def objective_value(self) -> float:
        return float(next(iter(self.objective_values.values())))


class _VerifiedCase(BenchmarkCase):
    def build_model(self, **kwargs: Any) -> object:
        return object()

    def solution_metrics(self, solution: Any, **kwargs: Any) -> dict[str, Any]:
        return {"objective": 1.0}

    def verify_solution(self, solution: Any, **kwargs: Any) -> SolutionVerification:
        return SolutionVerification.failed("independent verifier rejected the candidate")


class _ObjectiveMismatchCase(_VerifiedCase):
    def solution_metrics(self, solution: Any, **kwargs: Any) -> dict[str, Any]:
        return {"objective": 5.0}

    def verify_solution(self, solution: Any, **kwargs: Any) -> SolutionVerification:
        return SolutionVerification.accepted(objective=5.0)


def _case() -> _VerifiedCase:
    return _VerifiedCase(
        benchmark_id="custom_verification_test",
        family="sequence_transition_penalty",
        size={"items": 2},
        data={},
        reference={"objective": 0, "status": "optimal"},
        problem_description="Verifier contract test.",
        instance="verification_test",
        case_module=__name__,
        modeling_notes={"model_style": "test"},
    )


def test_runner_rejects_solver_claim_when_independent_verification_fails(monkeypatch: Any) -> None:
    import benchmarks.run as run_module

    monkeypatch.setattr(run_module, "build_strategy_config", lambda **_kwargs: object())
    monkeypatch.setattr(run_module, "_solve_model", lambda *_args, **_kwargs: _FakeSolution())

    [row] = run_benchmark_case(
        _case(),
        strategies=("ga",),
        allow_download=False,
        budget=LocalRunBudget(max_iterations=1, time_limit_s=0.1, population_size=4),
    )

    assert row["status"] == "verification_failed"
    assert row["feasible"] is False
    assert row["objective"] is None
    assert row["solver_reported_feasible"] is True
    assert row["solver_reported_objective"] == 1.0
    assert row["verification_status"] == "failed"
    assert row["verification_violations"] == ["independent verifier rejected the candidate"]


def test_runner_rejects_solver_objective_that_disagrees_with_independent_verification(
    monkeypatch: Any,
) -> None:
    import benchmarks.run as run_module

    monkeypatch.setattr(run_module, "build_strategy_config", lambda **_kwargs: object())
    monkeypatch.setattr(run_module, "_solve_model", lambda *_args, **_kwargs: _FakeSolution())

    [row] = run_benchmark_case(
        _ObjectiveMismatchCase(**_case().__dict__),
        strategies=("ga",),
        allow_download=False,
        budget=LocalRunBudget(max_iterations=1, time_limit_s=0.1, population_size=4),
    )

    assert row["status"] == "verification_failed"
    assert row["feasible"] is False
    assert row["objective"] is None
    assert row["solver_reported_objective"] == 1.0
    assert row["verification_passed"] is False
    assert row["verification_violations"] == ["solver_objective_mismatch:reported=1:verified=5"]


def test_observation_snapshot_rejects_solver_objective_mismatch() -> None:
    solution = _FakeSolution(
        objective_values={1: 5.0},
        solution_snapshots={
            "snapshot-1": SimpleNamespace(
                variable_values={},
                objective_values={1: 1.0},
                constraint_values={},
                feasible=True,
                violation_count=0,
                incumbent_found_at_s=0.5,
            )
        },
    )

    evidence = _verify_observation_snapshots(_ObjectiveMismatchCase(**_case().__dict__), solution, {})

    assert evidence["observation_verification_passed"] is False
    snapshot = evidence["solution_snapshots"]["snapshot-1"]
    assert snapshot["verification_status"] == "failed"
    assert snapshot["verification_passed"] is False
    assert snapshot["verification_violations"] == ["solver_objective_mismatch:reported=1:verified=5"]


def test_tsplib_defaults_to_the_graph_model_required_by_routing_search() -> None:
    from benchmarks.cases.registry import default_model_styles_for_family
    from benchmarks.cases.tsplib.tsp._domain import (
        DEFAULT_TSP_MODEL_STYLES,
        GRAPH_TSP_MODEL_STYLE,
        MODEL_STYLE,
    )

    assert MODEL_STYLE == GRAPH_TSP_MODEL_STYLE
    assert DEFAULT_TSP_MODEL_STYLES == (GRAPH_TSP_MODEL_STYLE,)
    assert default_model_styles_for_family("sequence_blackbox_tsp") == (GRAPH_TSP_MODEL_STYLE,)


def test_public_elapsed_time_excludes_case_setup(monkeypatch: Any) -> None:
    import benchmarks.run as run_module

    clock = iter((10.0, 13.0, 13.0, 18.0))
    monkeypatch.setattr(run_module, "perf_counter", lambda: next(clock))
    monkeypatch.setattr(run_module, "build_strategy_config", lambda **_kwargs: object())
    monkeypatch.setattr(run_module, "_solve_model", lambda *_args, **_kwargs: _FakeSolution())

    [row] = run_benchmark_case(
        _case(),
        strategies=("ga",),
        allow_download=False,
        budget=LocalRunBudget(max_iterations=1, time_limit_s=0.1, population_size=4),
    )

    assert row["case_setup_seconds"] == 3.0
    assert row["elapsed_seconds"] == 5.0


def test_base_case_verifier_is_explicitly_unsupported() -> None:
    verification = BenchmarkCase.verify_solution(_case(), _FakeSolution())

    assert verification.status == "unsupported"
    assert verification.passed is False
    assert verification.objective is None


def test_sequence_case_verifiers_recompute_objectives_and_reject_non_permutations() -> None:
    from benchmarks.cases.custom.steel_transition_sequence.toy import TOY
    from benchmarks.cases.qaplib.quadratic_assignment.nug import NUG12
    from benchmarks.cases.tsplib.tsp.berlin import BERLIN52

    for case in (TOY, NUG12, BERLIN52):
        case.build_model(allow_download=False)
        context = case._build_context()
        node_id = int(context.get("sequence_node_id", context.get("assignment_node_id")))
        size = int(next(iter(case.size.values())))
        identity = list(range(size))
        accepted = case.verify_solution(
            SimpleNamespace(variable_values={node_id: identity}, feasible=True, objective_value=-1.0)
        )
        rejected = case.verify_solution(
            SimpleNamespace(variable_values={node_id: [0] * size}, feasible=True, objective_value=-1.0)
        )

        assert accepted.status == "passed"
        assert accepted.objective is not None
        assert accepted.objective >= 0
        assert rejected.status == "failed"
        assert any("permutation" in item for item in rejected.violations)


def test_scheduling_verifiers_accept_serial_schedules_and_reject_bad_intervals() -> None:
    from benchmarks.cases.fjsplib.fjobshop.fattahi import SFJS01
    from benchmarks.cases.jsplib.jobshop.ft import FT06
    from benchmarks.cases.psplib.rcpsp.j90_1 import J90_1_1

    for case, values in (
        (FT06, _serial_job_shop_values(FT06)),
        (SFJS01, _serial_flexible_job_shop_values(SFJS01)),
        (J90_1_1, _serial_rcpsp_values(J90_1_1)),
    ):
        accepted = case.verify_solution(SimpleNamespace(variable_values=values, feasible=True, objective_value=-1.0))
        broken = dict(values)
        interval_node = next(node_id for node_id, value in broken.items() if isinstance(value, dict))
        broken[interval_node] = {**broken[interval_node], "end": broken[interval_node]["end"] + 1}
        rejected = case.verify_solution(SimpleNamespace(variable_values=broken, feasible=True, objective_value=-1.0))

        assert accepted.status == "passed"
        assert accepted.objective is not None
        assert rejected.status == "failed"
        assert any("interval" in item for item in rejected.violations)


def _serial_job_shop_values(case: Any) -> dict[int, Any]:
    case.build_model(allow_download=False)
    context = case._build_context()
    values: dict[int, Any] = {}
    cursor = 0
    for operation in sorted(context["instance"].operations, key=lambda item: (item.job, item.operation)):
        node_id = context["operation_node_ids"][(operation.job, operation.operation)]
        values[node_id] = {"start": cursor, "end": cursor + operation.duration, "length": operation.duration}
        cursor += operation.duration
    for machine, node_id in context["machine_sequence_node_ids"].items():
        values[node_id] = list(range(len(context["machine_operation_keys"][machine])))
    return values


def _serial_flexible_job_shop_values(case: Any) -> dict[int, Any]:
    case.build_model(allow_download=False)
    context = case._build_context()
    values: dict[int, Any] = {}
    cursor = 0
    for operation in sorted(context["instance"].operations, key=lambda item: item.operation_id):
        selected_machine = operation.candidates[0].machine
        selected_duration = operation.candidates[0].duration
        for candidate in operation.candidates:
            key = (operation.operation_id, candidate.machine)
            values[context["choice_node_ids"][key]] = candidate.machine == selected_machine
            values[context["interval_node_ids"][key]] = {
                "start": cursor,
                "end": cursor + candidate.duration,
                "length": candidate.duration,
            }
        cursor += selected_duration
    for machine, node_id in context["machine_sequence_node_ids"].items():
        values[node_id] = list(range(len(context["machine_candidate_keys"][machine])))
    return values


def _serial_rcpsp_values(case: Any) -> dict[int, Any]:
    case.build_model(allow_download=False)
    context = case._build_context()
    values: dict[int, Any] = {}
    cursor = 0
    for activity in context["instance"].activities:
        node_id = context["activity_node_ids"][activity.activity_id]
        values[node_id] = {"start": cursor, "end": cursor + activity.duration, "length": activity.duration}
        cursor += activity.duration
    return values


def test_mip_verifier_checks_bounds_constraints_integrality_and_objective(tmp_path: Any) -> None:
    from benchmarks.cases.miplib2017.linear_mip._domain import MipCase

    path = tmp_path / "simple.mps"
    path.write_text(
        """NAME SIMPLE
ROWS
 N COST
 G MINX
 L MAXX
COLUMNS
 X COST 2 MINX 1
 X MAXX 1
RHS
 RHS1 MINX 1 MAXX 3
BOUNDS
 UI BND X 3
ENDATA
""",
        encoding="utf-8",
    )
    case = MipCase(
        benchmark_id="miplib2017_simple",
        family="exact_linear_mip",
        size={"variables": 1, "constraints": 2},
        data={"local_path": str(path)},
        reference={"objective": 2.0, "status": "optimal"},
        problem_description="Simple verifier fixture.",
        instance="simple",
        case_module=__name__,
        modeling_notes={"model_style": "mps_linear_mp"},
    )
    case.build_model(allow_download=False)
    node_id = case._build_context()["variable_node_ids"]["X"]

    accepted = case.verify_solution(SimpleNamespace(variable_values={node_id: 2}, feasible=True, objective_value=-1.0))
    rejected = case.verify_solution(
        SimpleNamespace(variable_values={node_id: 0.5}, feasible=True, objective_value=-1.0)
    )

    assert accepted.status == "passed"
    assert accepted.objective == 4.0
    assert rejected.status == "failed"
    assert any("integer" in item or "constraint" in item for item in rejected.violations)
