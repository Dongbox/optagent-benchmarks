from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import csv
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

from benchmarks.cases.common import MODEL_STYLE_BY_FAMILY
from benchmarks.cases.registry import INSTANCE_COLLECTION_MODULES, implemented_families, run_case
from benchmarks.presentation.common import (
    DEFAULT_RUN_ROOT,
    EffectiveStrategyBudget,
    SEARCH_DIAGNOSTIC_KEYS,
    StrategyBudgetRequest,
    append_jsonl,
    ensure_run_dir,
    metadata_highlights,
    normalize_result_row,
    resolve_family_tier_budget,
    strategy_profile_name,
    utc_timestamp,
    write_json,
)
from benchmarks.presentation.telemetry import normalize_telemetry, write_anytime_jsonl, write_throughput_jsonl
from benchmarks.run import all_cases as load_case_rows, select_cases


# suite.py 是 presentation 层的标准 benchmark suite 评测场景调度器：
# 1. 从具体实例模块选择 case；
# 2. 解析 family-aware 策略矩阵和预算；
# 3. 通过 cases.registry 委托 benchmarks.run 的统一 case runner；
# 4. 对 row 做场景级归一化，并写出 JSONL/CSV/report/presentation feedback。
# 它不保存 case 私有建模逻辑，也不保存 case solve 共享函数。
RUNNER_SCENARIO_ID = "standard_benchmark_suite"
RUNNER_SCENARIO_KIND = "evaluation_scenario"
RUNNER_SCENARIO_DESCRIPTION = (
    "Standard artifact-writing benchmark suite for CI, calibration, strategy matrices, "
    "and dashboard publication inputs. Use benchmarks.run for lightweight local case tests."
)
IMPLEMENTED_FAMILIES = implemented_families()
DEFAULT_RUNNABLE_FAMILIES = ("interval_job_shop", "sequence_blackbox_tsp", "sequence_quadratic_assignment")
DEFAULT_STRATEGIES = ("ga", "alns")
DEFAULT_CANDIDATE_STRATEGIES = ("alns", "ga")
DEFAULT_PARALLEL_THREAD_COUNTS = (1, 2, 4, 8, 16)
SCHEDULING_FAMILIES = {"interval_job_shop", "cumulative_resource_scheduling"}
SCHEDULING_DEFAULT_STRATEGIES = ("ga", "alns")
SCHEDULING_STRATEGY_REPLACEMENTS = {"lns": "alns"}
SEQUENCE_DEFAULT_STRATEGIES = ("ga", "alns")
PUBLIC_STRATEGY_CONFIGS = (
    "LnsConfig",
    "AlnsConfig",
    "GaConfig",
)
DIRECT_EXACT_APIS = ("solve_milp",)
CORE_ROW_FIELDS = (
    "benchmark_schema_version",
    "benchmark_id",
    "family",
    "tier",
    "instance",
    "kind",
    "strategy",
    "strategy_profile",
    "budget_profile",
    "model_style",
    "status",
    "feasible",
    "objective",
    "best_cost",
    "reference_objective",
    "reference_cost",
    "reference_kind",
    "gap_abs",
    "gap_rel",
    "elapsed_seconds",
    "runtime_s",
    "time_to_best_seconds",
    "thread_count",
    "parallel_matrix_enabled",
    "effective_budget",
)
STRATEGY_ROW_OPTIONAL_FIELDS = (
    "strategy_config",
    "initial_cost",
    "improvement_abs",
    "improvement_rel",
    "improvement_per_second",
    "improvement_per_evaluation",
    "improvement_per_move",
    "moves_attempted",
    "moves_accepted",
    "evaluations",
    "delta_evaluations",
    "full_evaluations",
    "repairs_attempted",
    "repairs_succeeded",
)


def main() -> int:
    from benchmarks.bootstrap import prefer_local_development_paths

    prefer_local_development_paths()
    parser = argparse.ArgumentParser(
        description=(
            "Run the standard artifact-writing OptAgent benchmark suite presentation scenario. "
            "Use `python -m benchmarks.run` for lightweight local case tests."
        )
    )
    parser.add_argument("--family", action="append", dest="families", help="Benchmark family to run. Defaults to runnable smoke families.")
    parser.add_argument("--tier", action="append", dest="tiers", help="Benchmark tier to run. Defaults to smoke.")
    parser.add_argument("--case", action="append", dest="cases", help="Benchmark case id to run.")
    parser.add_argument(
        "--strategy",
        action="append",
        dest="strategies",
        help="Strategy to run. Defaults to family-aware ga/alns; scheduling lns requests are replaced by alns.",
    )
    parser.add_argument(
        "--default-candidate-matrix",
        action="store_true",
        help=(
            "Emit a default strategy candidate ranking from strategy rows. "
            "When no --strategy is provided, runs alns/ga candidates."
        ),
    )
    parser.add_argument(
        "--model-style",
        action="append",
        dest="model_styles",
        help="TSP model style to run. Repeat to compare blackbox and graph-native rows.",
    )
    parser.add_argument(
        "--parallel-matrix",
        action="store_true",
        help="Run the default benchmark thread matrix: 1, 2, 4, 8, 16.",
    )
    parser.add_argument(
        "--thread-count",
        action="append",
        type=int,
        dest="thread_counts",
        help="Thread count for a parallel matrix run. Repeat to override the default matrix.",
    )
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument(
        "--calibration-seed",
        action="append",
        type=int,
        dest="calibration_seeds",
        help=(
            "Run a multi-seed calibration wrapper. Repeat for each seed. "
            "When set, --seed is ignored and the default tier remains calibration unless --tier is provided."
        ),
    )
    parser.add_argument("--max-iterations", type=int, default=40)
    parser.add_argument("--time-limit-s", type=float, default=5.0)
    parser.add_argument("--population-size", type=int, default=10)
    parser.add_argument("--trace-limit", type=int, default=8)
    parser.add_argument("--no-download", action="store_true", help="Fail when a required public instance is not already cached.")
    parser.add_argument("--output-root", default=str(DEFAULT_RUN_ROOT), help="Directory where benchmark run artifacts are written.")
    parser.add_argument(
        "--list-inventory",
        action="store_true",
        help="Write and print benchmark inventory without executing solver routes.",
    )
    parser.add_argument("--timestamp", help="Explicit run directory name, primarily for tests.")
    args = parser.parse_args()

    families = tuple(args.families or DEFAULT_RUNNABLE_FAMILIES)
    tiers = tuple(args.tiers or ("calibration" if args.calibration_seeds else "smoke",))
    benchmark_ids = tuple(args.cases or ())
    strategies = tuple(
        args.strategies
        or (DEFAULT_CANDIDATE_STRATEGIES if args.default_candidate_matrix else DEFAULT_STRATEGIES)
    )
    thread_counts = tuple(
        args.thread_counts
        or (DEFAULT_PARALLEL_THREAD_COUNTS if args.parallel_matrix else ())
    )

    if args.list_inventory:
        inventory = build_benchmark_inventory(
            families=families,
            tiers=tiers,
            benchmark_ids=benchmark_ids,
            strategies=strategies,
            seed=args.seed,
            max_iterations=args.max_iterations,
            time_limit_s=args.time_limit_s,
            population_size=args.population_size,
            trace_limit=args.trace_limit,
            thread_counts=thread_counts or (1,),
        )
        run_dir = ensure_run_dir(args.output_root, timestamp=args.timestamp)
        write_json(run_dir / "inventory.json", inventory)
        write_json(run_dir / "run_metadata.json", inventory["environment"])
        summary = {
            "run_dir": str(run_dir),
            "mode": "inventory",
            "selected_case_count": inventory["selected_case_count"],
            "families": inventory["requested_families"],
            "tiers": inventory["requested_tiers"],
            "strategies": inventory["requested_strategies"],
            "artifacts": {
                "inventory": str(run_dir / "inventory.json"),
                "run_metadata": str(run_dir / "run_metadata.json"),
            },
        }
        write_json(run_dir / "summary.json", summary)
        print(json.dumps(summary, indent=2, ensure_ascii=True, sort_keys=True))
        return 0

    if args.calibration_seeds:
        summary = run_calibration_suite(
            output_root=args.output_root,
            families=families,
            tiers=tiers,
            benchmark_ids=benchmark_ids,
            strategies=strategies,
            seeds=tuple(args.calibration_seeds),
            max_iterations=args.max_iterations,
            time_limit_s=args.time_limit_s,
            population_size=args.population_size,
            trace_limit=args.trace_limit,
            allow_download=not args.no_download,
            model_styles=tuple(args.model_styles or ()),
            default_candidate_matrix=args.default_candidate_matrix,
            parallel_thread_counts=thread_counts,
            timestamp=args.timestamp,
        )
        print(json.dumps(summary, indent=2, ensure_ascii=True, sort_keys=True))
        return 0

    summary = run_benchmark_suite(
        output_root=args.output_root,
        families=families,
        tiers=tiers,
        benchmark_ids=benchmark_ids,
        strategies=strategies,
        seed=args.seed,
        max_iterations=args.max_iterations,
        time_limit_s=args.time_limit_s,
        population_size=args.population_size,
        trace_limit=args.trace_limit,
        allow_download=not args.no_download,
        model_styles=tuple(args.model_styles or ()),
        default_candidate_matrix=args.default_candidate_matrix,
        parallel_thread_counts=thread_counts,
        timestamp=args.timestamp,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=True, sort_keys=True))
    return 0


@dataclass(frozen=True)
class ScenarioCaseBudget:
    seed: int
    max_iterations: int
    time_limit_s: float
    population_size: int
    trace_limit: int
    thread_count: int = 1
    backend: str = "optx"



def run_benchmark_suite(
    *,
    case_rows: list[dict[str, Any]] | None = None,
    output_root: str | Path = DEFAULT_RUN_ROOT,
    families: tuple[str, ...] = DEFAULT_RUNNABLE_FAMILIES,
    tiers: tuple[str, ...] = ("smoke",),
    benchmark_ids: tuple[str, ...] = (),
    strategies: tuple[str, ...] = DEFAULT_STRATEGIES,
    seed: int = 11,
    max_iterations: int = 40,
    time_limit_s: float = 5.0,
    population_size: int = 10,
    trace_limit: int = 8,
    allow_download: bool = True,
    model_styles: tuple[str, ...] = (),
    default_candidate_matrix: bool = False,
    parallel_thread_counts: tuple[int, ...] = (),
    timestamp: str | None = None,
) -> dict[str, Any]:
    run_dir = ensure_run_dir(output_root, timestamp=timestamp)
    all_cases = list(case_rows) if case_rows is not None else load_case_rows()
    cases = select_cases(
        all_cases,
        families=families,
        tiers=tiers,
        benchmark_ids=benchmark_ids,
    )
    thread_counts = _normalize_thread_counts(parallel_thread_counts)
    budget_request = StrategyBudgetRequest(
        seed=seed,
        max_iterations=max_iterations,
        time_limit_s=time_limit_s,
        population_size=population_size,
        trace_limit=trace_limit,
        thread_count=1,
    )
    budget_matrix = _budget_matrix(families=families, tiers=tiers, request=budget_request)
    strategy_matrix = resolve_family_strategy_matrix(families=families, requested_strategies=strategies)
    strategy_plan = {
        family: tuple(item["strategy"] for item in item_plan["effective_strategies"])
        for family, item_plan in strategy_matrix.items()
    }
    strategy_substitutions = [
        {
            "family": family,
            "requested": list(strategies),
            "effective": list(effective),
            "reason": _strategy_plan_change_reason(family, strategy_matrix[family]),
        }
        for family, effective in strategy_plan.items()
        if tuple(strategies) != tuple(effective)
    ]
    config = {
        "runner_scenario_id": RUNNER_SCENARIO_ID,
        "runner_scenario_kind": RUNNER_SCENARIO_KIND,
        "runner_scenario_description": RUNNER_SCENARIO_DESCRIPTION,
        "case_source": "benchmarks.cases concrete instance modules",
        "instance_collection_modules": list(INSTANCE_COLLECTION_MODULES),
        "families": list(families),
        "tiers": list(tiers),
        "benchmark_ids": list(benchmark_ids),
        "strategies": list(strategies),
        "family_strategy_plan": {family: list(values) for family, values in strategy_plan.items()},
        "family_strategy_matrix": strategy_matrix,
        "strategy_substitutions": strategy_substitutions,
        "default_candidate_matrix": bool(default_candidate_matrix),
        "parallel_matrix_enabled": bool(thread_counts),
        "parallel_thread_counts": list(thread_counts or (1,)),
        "model_styles": list(model_styles),
        "budget": asdict(budget_request),
        "budget_policy": "family_tier_ceiling_v1",
        "family_budgets": budget_matrix,
        "allow_download": allow_download,
        "implemented_families": sorted(IMPLEMENTED_FAMILIES),
        "environment": build_run_environment_metadata(),
        "python": sys.version,
        "platform": platform.platform(),
    }
    write_json(run_dir / "config.json", config)
    write_json(run_dir / "inventory.json", build_benchmark_inventory(
        case_rows=all_cases,
        families=families,
        tiers=tiers,
        benchmark_ids=benchmark_ids,
        strategies=strategies,
        seed=seed,
        max_iterations=max_iterations,
        time_limit_s=time_limit_s,
        population_size=population_size,
        trace_limit=trace_limit,
        thread_counts=thread_counts or (1,),
    ))
    write_json(run_dir / "run_metadata.json", config["environment"])

    rows: list[dict[str, Any]] = []
    skipped_cases: list[dict[str, Any]] = []
    for case in cases:
        family = case["family"]
        if family not in IMPLEMENTED_FAMILIES:
            skipped_cases.append(
                {
                    "benchmark_id": case["benchmark_id"],
                    "family": family,
                    "reason": "family runner is not implemented yet",
                }
            )
            continue
        for thread_count in thread_counts or (1,):
            effective_budget = resolve_family_tier_budget(
                family=family,
                tier=str(case.get("tier") or "smoke"),
                request=StrategyBudgetRequest(
                    seed=seed,
                    max_iterations=max_iterations,
                    time_limit_s=time_limit_s,
                    population_size=population_size,
                    trace_limit=trace_limit,
                    thread_count=thread_count,
                ),
            )
            case_rows = _run_case_implementation(
                case,
                strategies=strategies if family == "exact_linear_mip" else strategy_plan[family],
                budget=_scenario_case_budget(family=family, effective_budget=effective_budget),
                allow_download=allow_download,
                model_styles=model_styles,
            )
            case_rows = [
                _normalize_case_row(
                    row,
                    effective_budget,
                    parallel_matrix_enabled=bool(thread_counts),
                    route_plan=strategy_matrix.get(family, {}),
                )
                for row in case_rows
            ]
            append_jsonl(run_dir / "results.jsonl", case_rows)
            append_jsonl(run_dir / "rows.jsonl", case_rows)
            rows.extend(case_rows)

    summary = build_summary(
        run_dir=run_dir,
        config=config,
        selected_case_count=len(cases),
        skipped_cases=skipped_cases,
        rows=rows,
    )
    write_json(run_dir / "summary.json", summary)
    write_results_csv(run_dir / "results.csv", rows)
    write_anytime_jsonl(run_dir / "anytime.jsonl", rows)
    write_anytime_jsonl(run_dir / "curves.jsonl", rows)
    write_throughput_jsonl(run_dir / "throughput.jsonl", rows)
    write_json(run_dir / "strategy_feedback.json", summary["strategy_feedback"])
    (run_dir / "report.md").write_text(render_report(summary, rows), encoding="utf-8")
    return summary


def run_calibration_suite(
    *,
    seeds: tuple[int, ...],
    case_rows: list[dict[str, Any]] | None = None,
    output_root: str | Path = DEFAULT_RUN_ROOT,
    families: tuple[str, ...] = DEFAULT_RUNNABLE_FAMILIES,
    tiers: tuple[str, ...] = ("calibration",),
    benchmark_ids: tuple[str, ...] = (),
    strategies: tuple[str, ...] = DEFAULT_STRATEGIES,
    max_iterations: int = 40,
    time_limit_s: float = 5.0,
    population_size: int = 10,
    trace_limit: int = 8,
    allow_download: bool = True,
    model_styles: tuple[str, ...] = (),
    default_candidate_matrix: bool = False,
    parallel_thread_counts: tuple[int, ...] = (),
    timestamp: str | None = None,
) -> dict[str, Any]:
    if not seeds:
        raise ValueError("calibration seeds must not be empty")
    calibration_dir = ensure_run_dir(output_root, timestamp=timestamp)
    seed_summaries: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    for seed in seeds:
        summary = run_benchmark_suite(
            case_rows=case_rows,
            output_root=calibration_dir,
            families=families,
            tiers=tiers,
            benchmark_ids=benchmark_ids,
            strategies=strategies,
            seed=seed,
            max_iterations=max_iterations,
            time_limit_s=time_limit_s,
            population_size=population_size,
            trace_limit=trace_limit,
            allow_download=allow_download,
            model_styles=model_styles,
            default_candidate_matrix=default_candidate_matrix,
            parallel_thread_counts=parallel_thread_counts,
            timestamp=f"seed-{seed}",
        )
        seed_summaries.append(summary)
        rows.extend(_load_run_rows(Path(summary["run_dir"])))
    calibration = build_calibration_summary(
        calibration_dir=calibration_dir,
        seed_summaries=seed_summaries,
        rows=rows,
        seeds=seeds,
        families=families,
        tiers=tiers,
        strategies=strategies,
    )
    append_jsonl(calibration_dir / "rows.jsonl", rows)
    write_json(calibration_dir / "calibration_summary.json", calibration)
    write_json(calibration_dir / "strategy_feedback.json", calibration["strategy_feedback"])
    return calibration


def _budget_matrix(
    *,
    families: tuple[str, ...],
    tiers: tuple[str, ...],
    request: StrategyBudgetRequest,
) -> dict[str, dict[str, dict[str, Any]]]:
    return {
        family: {
            tier: resolve_family_tier_budget(
                family=family,
                tier=tier,
                request=request,
            ).to_dict()
            for tier in tiers
        }
        for family in families
    }


def _normalize_thread_counts(thread_counts: tuple[int, ...]) -> tuple[int, ...]:
    if not thread_counts:
        return ()
    normalized = sorted({int(value) for value in thread_counts})
    if any(value < 1 for value in normalized):
        raise ValueError("parallel thread counts must be >= 1")
    return tuple(normalized)


def _scenario_case_budget(*, family: str, effective_budget: EffectiveStrategyBudget) -> ScenarioCaseBudget:
    return ScenarioCaseBudget(
        seed=effective_budget.seed,
        max_iterations=0 if family == "exact_linear_mip" else effective_budget.max_iterations,
        time_limit_s=effective_budget.exact_time_limit_s or effective_budget.time_limit_s,
        population_size=0 if family == "exact_linear_mip" else effective_budget.population_size,
        trace_limit=0 if family == "exact_linear_mip" else effective_budget.trace_limit,
        thread_count=effective_budget.thread_count,
        backend="optx",
    )


def _effective_strategies_for_family(family: str, requested: tuple[str, ...]) -> tuple[str, ...]:
    if family == "exact_linear_mip":
        return requested
    defaults = SCHEDULING_DEFAULT_STRATEGIES if family in SCHEDULING_FAMILIES else SEQUENCE_DEFAULT_STRATEGIES
    source = requested or defaults
    effective: list[str] = []
    for strategy in source:
        replacement = (
            SCHEDULING_STRATEGY_REPLACEMENTS.get(strategy, strategy)
            if family in SCHEDULING_FAMILIES
            else strategy
        )
        if replacement not in effective:
            effective.append(replacement)
    return tuple(effective)


def _strategy_plan_change_reason(family: str, route_plan: dict[str, Any]) -> str:
    if family == "exact_linear_mip":
        return "exact_linear_mip is exact-only; heuristic requests are recorded but not executed"
    reasons = [
        str(decision.get("reason"))
        for decision in route_plan.get("route_decisions", [])
        if decision.get("decision") == "substituted" and decision.get("reason")
    ]
    return reasons[0] if reasons else "requested strategies were resolved through the family strategy matrix"


def build_benchmark_inventory(
    *,
    case_rows: list[dict[str, Any]] | None = None,
    families: tuple[str, ...] = DEFAULT_RUNNABLE_FAMILIES,
    tiers: tuple[str, ...] = ("smoke",),
    benchmark_ids: tuple[str, ...] = (),
    strategies: tuple[str, ...] = DEFAULT_STRATEGIES,
    seed: int = 11,
    max_iterations: int = 40,
    time_limit_s: float = 5.0,
    population_size: int = 10,
    trace_limit: int = 8,
    thread_counts: tuple[int, ...] = (1,),
) -> dict[str, Any]:
    """Build a no-solve benchmark inventory from concrete instance modules."""

    all_cases = list(case_rows) if case_rows is not None else load_case_rows()
    selected_cases = select_cases(
        all_cases,
        families=families,
        tiers=tiers,
        benchmark_ids=benchmark_ids,
    )
    budget_request = StrategyBudgetRequest(
        seed=seed,
        max_iterations=max_iterations,
        time_limit_s=time_limit_s,
        population_size=population_size,
        trace_limit=trace_limit,
        thread_count=1,
    )
    normalized_thread_counts = _normalize_thread_counts(thread_counts) or (1,)
    strategy_matrix = resolve_family_strategy_matrix(families=families, requested_strategies=strategies)
    family_strategy_plan = {
        family: tuple(item["strategy"] for item in item_plan["effective_strategies"])
        for family, item_plan in strategy_matrix.items()
    }
    return {
        "runner_scenario_id": RUNNER_SCENARIO_ID,
        "runner_scenario_kind": RUNNER_SCENARIO_KIND,
        "runner_scenario_description": RUNNER_SCENARIO_DESCRIPTION,
        "case_source": "benchmarks.cases concrete instance modules",
        "case_count": len(all_cases),
        "selected_case_count": len(selected_cases),
        "implemented_families": sorted(IMPLEMENTED_FAMILIES),
        "default_runnable_families": list(DEFAULT_RUNNABLE_FAMILIES),
        "requested_families": list(families),
        "requested_tiers": list(tiers),
        "requested_benchmark_ids": list(benchmark_ids),
        "public_strategy_configs": list(PUBLIC_STRATEGY_CONFIGS),
        "direct_exact_apis": list(DIRECT_EXACT_APIS),
        "requested_strategies": list(strategies),
        "family_strategy_plan": {family: list(values) for family, values in family_strategy_plan.items()},
        "family_strategy_matrix": strategy_matrix,
        "strategy_substitution_rules": {
            "scheduling_families": sorted(SCHEDULING_FAMILIES),
            "replacements": dict(SCHEDULING_STRATEGY_REPLACEMENTS),
            "reason": (
                "standalone lns does not currently produce feasible scheduling benchmark rows; "
                "alns is the repairable scheduling search route"
            ),
        },
        "exact_only_families": ["exact_linear_mip"],
        "family_route_matrix": _family_route_matrix(),
        "families": _inventory_family_rows(all_cases),
        "selected_cases": [_inventory_case_row(case) for case in selected_cases],
        "row_schema": {
            "version": 2,
            "core_fields": list(CORE_ROW_FIELDS),
            "strategy_optional_fields": list(STRATEGY_ROW_OPTIONAL_FIELDS),
            "diagnostic_metadata_fields": list(SEARCH_DIAGNOSTIC_KEYS),
            "canonical_row_stream": "rows.jsonl",
            "legacy_row_stream": "results.jsonl",
        },
        "budget_policy": "family_tier_ceiling_v1",
        "family_budgets": _budget_matrix(families=families, tiers=tiers, request=budget_request),
        "thread_counts": list(normalized_thread_counts),
        "environment": build_run_environment_metadata(),
    }


def build_run_environment_metadata() -> dict[str, Any]:
    return {
        "python": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "native_extension_spec": _find_module_origin("_optagent_native"),
        "optagent_spec": _find_module_origin("optagent"),
        "git": _git_metadata(),
    }


def _find_module_origin(module_name: str) -> str | None:
    try:
        import importlib.util

        spec = importlib.util.find_spec(module_name)
    except Exception:
        return None
    if spec is None:
        return None
    return spec.origin


def _git_metadata() -> dict[str, Any]:
    def run_git(*args: str) -> str | None:
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=Path(__file__).resolve().parents[2],
                capture_output=True,
                text=True,
                check=False,
            )
        except Exception:
            return None
        if result.returncode != 0:
            return None
        return result.stdout.strip()

    status = run_git("status", "--short")
    return {
        "commit": run_git("rev-parse", "HEAD"),
        "branch": run_git("branch", "--show-current"),
        "is_dirty": bool(status),
        "status_short": status,
    }


def _family_route_matrix() -> dict[str, dict[str, Any]]:
    return {
        "exact_linear_mip": {
            "routes": ["solve_milp backend=optx"],
            "exact_only": True,
            "ignored_heuristic_metadata": "mip_heuristic_route_enabled=false",
        },
        "interval_job_shop": {
            "routes": ["GaConfig", "AlnsConfig"],
            "strategy_replacements": dict(SCHEDULING_STRATEGY_REPLACEMENTS),
        },
        "cumulative_resource_scheduling": {
            "routes": ["GaConfig", "AlnsConfig"],
            "strategy_replacements": dict(SCHEDULING_STRATEGY_REPLACEMENTS),
        },
        "sequence_blackbox_tsp": {
            "routes": ["GaConfig", "AlnsConfig"],
            "strategy_replacements": {},
        },
        "sequence_quadratic_assignment": {
            "routes": ["GaConfig", "AlnsConfig"],
            "strategy_replacements": {},
        },
    }


def resolve_family_strategy_matrix(
    *,
    families: tuple[str, ...],
    requested_strategies: tuple[str, ...],
) -> dict[str, dict[str, Any]]:
    """Resolve requested strategies into family-valid executable routes."""

    matrix: dict[str, dict[str, Any]] = {}
    for family in families:
        source = requested_strategies or (
            SCHEDULING_DEFAULT_STRATEGIES if family in SCHEDULING_FAMILIES else SEQUENCE_DEFAULT_STRATEGIES
        )
        effective: list[str] = []
        decisions: list[dict[str, Any]] = []
        if family == "exact_linear_mip":
            for strategy in source:
                decisions.append(
                    {
                        "family": family,
                        "requested_strategy": strategy,
                        "effective_strategy": "optx",
                        "decision": "ignored",
                        "reason": "exact_linear_mip is exact-only; heuristic requests are recorded but not executed",
                    }
                )
            effective = ["optx"]
        else:
            for strategy in source:
                replacement = (
                    SCHEDULING_STRATEGY_REPLACEMENTS.get(strategy, strategy)
                    if family in SCHEDULING_FAMILIES
                    else strategy
                )
                decision = "used" if replacement == strategy else "substituted"
                decisions.append(
                    {
                        "family": family,
                        "requested_strategy": strategy,
                        "effective_strategy": replacement,
                        "decision": decision,
                        "reason": (
                            "standalone lns does not currently produce feasible scheduling benchmark rows; "
                            "alns is the repairable scheduling search route"
                            if decision == "substituted"
                            else "valid family strategy"
                        ),
                    }
                )
                if replacement not in effective:
                    effective.append(replacement)
        matrix[family] = {
            "family": family,
            "requested_strategies": list(source),
            "effective_strategies": [
                {
                    "strategy": strategy,
                    "strategy_profile": strategy_profile_name(
                        family=family,
                        strategy=strategy,
                        kind="exact_baseline" if family == "exact_linear_mip" else "strategy_run",
                    ),
                }
                for strategy in effective
            ],
            "route_decisions": decisions,
            "exact_only": family == "exact_linear_mip",
            "model_style": MODEL_STYLE_BY_FAMILY.get(family),
        }
    return matrix


def _inventory_family_rows(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_family: dict[str, dict[str, Any]] = {}
    for case in cases:
        family = str(case.get("family") or "")
        if not family:
            continue
        row = by_family.setdefault(
            family,
            {
                "family": family,
                "implemented": family in IMPLEMENTED_FAMILIES,
                "case_count": 0,
                "tiers": set(),
                "benchmark_ids": [],
                "model_style": None,
                "route_matrix": _family_route_matrix().get(family, {}),
            },
        )
        row["case_count"] += 1
        row["tiers"].add(str(case.get("tier") or ""))
        row["benchmark_ids"].append(str(case.get("benchmark_id") or ""))
        row["model_style"] = row["model_style"] or case.get("model_style")
    rows = []
    for row in by_family.values():
        rows.append({
            **row,
            "tiers": sorted(value for value in row["tiers"] if value),
            "benchmark_ids": sorted(value for value in row["benchmark_ids"] if value),
        })
    return sorted(rows, key=lambda item: item["family"])


def _run_case_implementation(
    case: dict[str, Any],
    *,
    strategies: tuple[str, ...],
    budget: Any,
    allow_download: bool,
    model_styles: tuple[str, ...],
) -> list[dict[str, Any]]:
    family = str(case["family"])
    kwargs: dict[str, Any] = {
        "strategies": strategies,
        "budget": budget,
        "allow_download": allow_download,
    }
    if family == "sequence_blackbox_tsp":
        kwargs["model_styles"] = model_styles
    return run_case(case, **kwargs)


def _inventory_case_row(case: dict[str, Any]) -> dict[str, Any]:
    reference = case.get("reference") if isinstance(case.get("reference"), dict) else {}
    return {
        "benchmark_id": case.get("benchmark_id"),
        "family": case.get("family"),
        "tier": case.get("tier"),
        "instance": case.get("instance"),
        "reference_kind": reference.get("value_kind") or case.get("reference_kind"),
        "reference_objective": reference.get("objective") or case.get("reference_objective"),
        "model_style": case.get("model_style"),
        "implemented": case.get("family") in IMPLEMENTED_FAMILIES,
    }


def _normalize_case_row(
    row: dict[str, Any],
    budget: EffectiveStrategyBudget,
    *,
    parallel_matrix_enabled: bool = False,
    route_plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    family = str(row.get("family") or budget.family)
    row["problem_family"] = family
    row["budget_profile"] = budget.profile
    row["effective_max_iterations"] = budget.max_iterations
    row["effective_time_limit_s"] = budget.time_limit_s
    row["effective_population_size"] = budget.population_size
    row["effective_trace_limit"] = budget.trace_limit
    row["thread_count"] = budget.thread_count
    row["parallel_matrix_enabled"] = bool(parallel_matrix_enabled)
    if budget.exact_time_limit_s is not None:
        row["effective_exact_time_limit_s"] = budget.exact_time_limit_s
    row["effective_budget"] = budget.to_dict()
    if route_plan:
        row["route_decision"] = _route_decision_for_row(row, route_plan)
        row["family_exact_only"] = bool(route_plan.get("exact_only", False))
        metadata = row.setdefault("metadata", {})
        if isinstance(metadata, dict):
            metadata.setdefault("route_decision", row["route_decision"])
            metadata.setdefault("family_exact_only", row["family_exact_only"])
    metadata = row.get("metadata")
    if isinstance(metadata, dict):
        metadata.setdefault("budget_profile", budget.profile)
        metadata.setdefault("effective_budget", budget.to_dict())
        metadata.setdefault("thread_count", budget.thread_count)
        metadata.setdefault("parallel_matrix_enabled", bool(parallel_matrix_enabled))
    return normalize_telemetry(normalize_result_row(row))


def _route_decision_for_row(row: dict[str, Any], route_plan: dict[str, Any]) -> dict[str, Any]:
    strategy = str(row.get("strategy") or "")
    if route_plan.get("exact_only"):
        return {
            "decision": "exact_baseline",
            "effective_strategy": strategy,
            "reason": "exact-only family route",
        }
    for decision in route_plan.get("route_decisions", []):
        if decision.get("effective_strategy") == strategy:
            return dict(decision)
    return {
        "decision": "used",
        "effective_strategy": strategy,
        "reason": "valid family strategy",
    }


def _profile_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        profile = str(row.get("strategy_profile") or "")
        if not profile:
            continue
        counts[profile] = counts.get(profile, 0) + 1
    return counts


def build_summary(
    *,
    run_dir: Path,
    config: dict[str, Any],
    selected_case_count: int,
    skipped_cases: list[dict[str, Any]],
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    successful_rows = [
        row
        for row in rows
        if row.get("status") != "error" and row.get("objective") is not None and row.get("feasible") is True
    ]
    error_rows = [row for row in rows if row.get("status") == "error"]
    non_feasible_rows = [row for row in rows if row.get("status") != "error" and row.get("feasible") is not True]
    best_by_case: dict[str, dict[str, Any]] = {}
    for row in successful_rows:
        key = str(row["benchmark_id"])
        current = best_by_case.get(key)
        if current is None or (float(row["objective"]), float(row["elapsed_seconds"])) < (
            float(current["objective"]),
            float(current["elapsed_seconds"]),
        ):
            best_by_case[key] = row

    return {
        "run_dir": str(run_dir),
        "selected_case_count": selected_case_count,
        "executed_case_count": len({row["benchmark_id"] for row in rows}),
        "skipped_case_count": len(skipped_cases),
        "strategy_run_count": len(rows),
        "strategy_row_count": sum(1 for row in rows if row.get("kind") == "strategy_run"),
        "exact_baseline_row_count": sum(1 for row in rows if row.get("kind") == "exact_baseline"),
        "successful_run_count": len(successful_rows),
        "error_run_count": len(error_rows),
        "non_feasible_run_count": len(non_feasible_rows),
        "families": list(config["families"]),
        "tiers": list(config["tiers"]),
        "strategies": list(config["strategies"]),
        "family_strategy_plan": config.get("family_strategy_plan", {}),
        "strategy_substitutions": config.get("strategy_substitutions", []),
        "family_strategy_matrix": config.get("family_strategy_matrix", {}),
        "parallel_matrix_enabled": bool(config.get("parallel_matrix_enabled", False)),
        "parallel_thread_counts": list(config.get("parallel_thread_counts", [1])),
        "parallel_matrix": (
            build_parallel_matrix(rows)
            if config.get("parallel_matrix_enabled", False)
            else {"enabled": False, "reason": "not requested", "groups": []}
        ),
        "default_candidate_matrix_enabled": bool(config.get("default_candidate_matrix", False)),
        "default_candidate_matrix": (
            build_default_candidate_matrix(rows)
            if config.get("default_candidate_matrix", False)
            else {"enabled": False, "reason": "not requested", "ranked_strategies": []}
        ),
        "budget": dict(config["budget"]),
        "budget_policy": config.get("budget_policy"),
        "family_budgets": config.get("family_budgets", {}),
        "profile_counts": _profile_counts(rows),
        "family_improvement_summary": _family_improvement_summary(rows),
        "calibration_summary": build_calibration_row_summary(rows),
        "regression_gates": build_regression_gate_summary(rows),
        "strategy_feedback": build_strategy_feedback(rows, config=config),
        "skipped_cases": skipped_cases,
        "best_by_case": {
            key: {
                "strategy": row["strategy"],
                "strategy_profile": row.get("strategy_profile"),
                "model_style": row.get("model_style"),
                "kind": row.get("kind"),
                "objective": row["objective"],
                "reference_objective": row.get("reference_objective"),
                "gap_abs": row.get("gap_abs"),
                "gap_rel": row.get("gap_rel"),
                "elapsed_seconds": row.get("elapsed_seconds"),
            }
            for key, row in sorted(best_by_case.items())
        },
        "artifacts": {
            "config": str(run_dir / "config.json"),
            "inventory": str(run_dir / "inventory.json"),
            "run_metadata": str(run_dir / "run_metadata.json"),
            "rows_jsonl": str(run_dir / "rows.jsonl"),
            "results_jsonl": str(run_dir / "results.jsonl"),
            "results_csv": str(run_dir / "results.csv"),
            "anytime_jsonl": str(run_dir / "anytime.jsonl"),
            "curves_jsonl": str(run_dir / "curves.jsonl"),
            "throughput_jsonl": str(run_dir / "throughput.jsonl"),
            "strategy_feedback": str(run_dir / "strategy_feedback.json"),
            "summary": str(run_dir / "summary.json"),
            "report": str(run_dir / "report.md"),
        },
    }


def build_calibration_summary(
    *,
    calibration_dir: Path,
    seed_summaries: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    seeds: tuple[int, ...],
    families: tuple[str, ...],
    tiers: tuple[str, ...],
    strategies: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "calibration_dir": str(calibration_dir),
        "seeds": list(seeds),
        "seed_count": len(seeds),
        "families": list(families),
        "tiers": list(tiers),
        "strategies": list(strategies),
        "seed_runs": [
            {
                "seed": seeds[index],
                "run_dir": summary["run_dir"],
                "successful_run_count": summary.get("successful_run_count", 0),
                "error_run_count": summary.get("error_run_count", 0),
                "non_feasible_run_count": summary.get("non_feasible_run_count", 0),
            }
            for index, summary in enumerate(seed_summaries)
        ],
        "row_count": len(rows),
        "calibration_summary": build_calibration_row_summary(rows),
        "regression_gates": build_regression_gate_summary(rows),
        "strategy_feedback": build_strategy_feedback(rows, config={
            "families": list(families),
            "tiers": list(tiers),
            "strategies": list(strategies),
            "budget_policy": "family_tier_ceiling_v1",
        }),
        "artifacts": {
            "rows_jsonl": str(calibration_dir / "rows.jsonl"),
            "calibration_summary": str(calibration_dir / "calibration_summary.json"),
            "strategy_feedback": str(calibration_dir / "strategy_feedback.json"),
        },
    }


def build_calibration_row_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        key = (
            str(row.get("family") or ""),
            str(row.get("model_style") or ""),
            str(row.get("strategy") or ""),
            str(row.get("strategy_profile") or ""),
        )
        groups.setdefault(key, []).append(row)
    result = []
    for (family, model_style, strategy, profile), group_rows in sorted(groups.items()):
        objectives = _numeric_values(group_rows, "objective")
        gaps = _numeric_values(group_rows, "gap_rel")
        elapsed = _numeric_values(group_rows, "elapsed_seconds")
        result.append(
            {
                "family": family,
                "model_style": model_style,
                "strategy": strategy,
                "strategy_profile": profile,
                "row_count": len(group_rows),
                "success_count": sum(1 for row in group_rows if row.get("status") != "error" and row.get("feasible") is True),
                "failure_count": sum(1 for row in group_rows if row.get("status") == "error"),
                "non_feasible_count": sum(1 for row in group_rows if row.get("status") != "error" and row.get("feasible") is not True),
                "feasible_rate": _safe_ratio(sum(1 for row in group_rows if row.get("feasible") is True), len(group_rows)),
                "objective": _distribution(objectives),
                "gap_rel": _distribution(gaps),
                "elapsed_seconds": _distribution(elapsed),
                "best_objective": min(objectives) if objectives else None,
                "worst_objective": max(objectives) if objectives else None,
                "median_objective": _median(sorted(objectives)) if objectives else None,
            }
        )
    return {
        "group_count": len(result),
        "groups": result,
    }


def build_regression_gate_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups = build_calibration_row_summary(rows)["groups"]
    checks = {
        "schema_completeness": _single_run_schema_gate(rows),
        "feasible_rate": _single_run_feasible_gate(groups),
        "quality": _single_run_quality_gate(groups),
        "runtime": _single_run_runtime_gate(groups),
    }
    return {
        "overall_status": "pass" if all(check["status"] == "pass" for check in checks.values()) else "fail",
        "checks": checks,
        "thresholds": {
            "min_feasible_rate": 0.5,
            "max_gap_rel": 10.0,
            "max_median_runtime_s": None,
        },
    }


def build_strategy_feedback(rows: list[dict[str, Any]], *, config: dict[str, Any]) -> dict[str, Any]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(
            (str(row.get("family") or "unknown"), str(row.get("model_style") or "")),
            [],
        ).append(row)
    groups = []
    for (family, model_style), group_rows in sorted(grouped.items()):
        candidates = [_feedback_candidate(strategy, rows_for_strategy) for strategy, rows_for_strategy in _rows_by_strategy(group_rows).items()]
        candidates.sort(key=_feedback_sort_key)
        for rank, candidate in enumerate(candidates, start=1):
            candidate["rank"] = rank
            candidate["recommended"] = rank == 1
        recommendation = candidates[0] if candidates else None
        groups.append(
            {
                "family": family,
                "model_style": model_style,
                "row_count": len(group_rows),
                "recommendation": recommendation,
                "candidates": candidates,
            }
        )
    return {
        "schema_version": 1,
        "generated_from": "benchmark_suite_summary",
        "budget_policy": config.get("budget_policy"),
        "families": list(config.get("families", [])),
        "tiers": list(config.get("tiers", [])),
        "explicit_user_strategy_override_policy": "feedback never overrides an explicit user-selected strategy",
        "reference_policy": "external optimum or public best-known references only; local best is diagnostic",
        "freshness": {
            "created_at_utc": utc_timestamp(),
            "source_run_tier": list(config.get("tiers", [])),
        },
        "groups": groups,
    }


def build_default_candidate_matrix(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Rank strategy candidates by coverage, feasibility, quality, and runtime."""

    strategy_rows = [
        row
        for row in rows
        if row.get("kind") == "strategy_run" and int(row.get("thread_count") or 1) == 1
    ]
    by_strategy: dict[str, list[dict[str, Any]]] = {}
    for row in strategy_rows:
        strategy = str(row.get("strategy") or "")
        if strategy:
            by_strategy.setdefault(strategy, []).append(row)

    ranked = [
        _default_candidate_score(strategy, strategy_rows)
        for strategy, strategy_rows in sorted(by_strategy.items())
    ]
    ranked.sort(key=_default_candidate_sort_key)
    for index, row in enumerate(ranked, start=1):
        row["rank"] = index
        row["recommended"] = index == 1
    return {
        "enabled": True,
        "selection_policy": "feasible_coverage_then_error_then_gap_then_time_then_improvement_v1",
        "ranked_strategies": ranked,
        "recommended_strategy": ranked[0]["strategy"] if ranked else None,
        "strategy_count": len(ranked),
        "row_count": len(strategy_rows),
    }


def build_parallel_matrix(rows: list[dict[str, Any]]) -> dict[str, Any]:
    matrix_rows = [row for row in rows if row.get("parallel_matrix_enabled")]
    by_group: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = {}
    for row in matrix_rows:
        key = (
            str(row.get("benchmark_id") or ""),
            str(row.get("strategy") or ""),
            str(row.get("strategy_profile") or ""),
            str(row.get("model_style") or ""),
            str(row.get("kind") or ""),
        )
        by_group.setdefault(key, []).append(row)

    groups = []
    for key, group_rows in sorted(by_group.items()):
        baseline = _thread_row(group_rows, 1)
        rows_by_thread = []
        for row in sorted(group_rows, key=lambda item: int(item.get("thread_count") or 1)):
            rows_by_thread.append(_parallel_matrix_row(row, baseline))
        groups.append(
            {
                "benchmark_id": key[0],
                "strategy": key[1],
                "strategy_profile": key[2],
                "model_style": key[3],
                "kind": key[4],
                "baseline_thread_count": 1,
                "has_baseline": baseline is not None,
                "rows": rows_by_thread,
            }
        )
    return {
        "enabled": True,
        "thread_counts": sorted({int(row.get("thread_count") or 1) for row in matrix_rows}),
        "group_count": len(groups),
        "groups": groups,
    }


def _thread_row(rows: list[dict[str, Any]], thread_count: int) -> dict[str, Any] | None:
    for row in rows:
        if int(row.get("thread_count") or 1) == thread_count:
            return row
    return None


def _parallel_matrix_row(row: dict[str, Any], baseline: dict[str, Any] | None) -> dict[str, Any]:
    baseline_elapsed = _float_or_none(baseline.get("elapsed_seconds")) if baseline else None
    elapsed = _float_or_none(row.get("elapsed_seconds"))
    thread_count = int(row.get("thread_count") or 1)
    speedup = baseline_elapsed / elapsed if baseline_elapsed is not None and elapsed and elapsed > 0 else None
    efficiency = speedup / thread_count if speedup is not None and thread_count > 0 else None
    throughput_speedup = _throughput_speedup(row, baseline)
    return {
        "thread_count": thread_count,
        "status": row.get("status"),
        "feasible": row.get("feasible"),
        "objective": row.get("objective"),
        "gap_rel": row.get("gap_rel"),
        "elapsed_seconds": row.get("elapsed_seconds"),
        "speedup": speedup,
        "efficiency": efficiency,
        "quality_delta_vs_1_thread": _delta_float(row, baseline, "objective"),
        "gap_delta_vs_1_thread": _delta_float(row, baseline, "gap_rel"),
        "throughput_speedup": throughput_speedup,
    }


def _throughput_speedup(row: dict[str, Any], baseline: dict[str, Any] | None) -> float | None:
    if baseline is None:
        return None
    for field in (
        "evaluations_per_s",
        "moves_attempted_per_s",
        "delta_evaluations_per_s",
        "repairs_attempted_per_s",
    ):
        current = _float_or_none(row.get(field))
        base = _float_or_none(baseline.get(field))
        if current is not None and base is not None and base > 0:
            return current / base
    return None


def _delta_float(
    row: dict[str, Any],
    baseline: dict[str, Any] | None,
    field: str,
) -> float | None:
    if baseline is None:
        return None
    current = _float_or_none(row.get(field))
    base = _float_or_none(baseline.get(field))
    if current is None or base is None:
        return None
    return current - base


def _default_candidate_score(strategy: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    successful = [
        row
        for row in rows
        if row.get("status") != "error" and row.get("feasible") is True and row.get("objective") is not None
    ]
    error_rows = [row for row in rows if row.get("status") == "error"]
    non_feasible = [row for row in rows if row.get("status") != "error" and row.get("feasible") is not True]
    gap_values = [
        float(row["gap_rel"])
        for row in successful
        if row.get("gap_rel") is not None
    ]
    elapsed_values = [
        float(row["elapsed_seconds"])
        for row in rows
        if row.get("elapsed_seconds") is not None
    ]
    improvement_values = [
        float(row["improvement_per_second"])
        for row in successful
        if row.get("improvement_per_second") is not None
    ]
    row_count = len(rows)
    successful_count = len(successful)
    feasible_rate = successful_count / row_count if row_count else 0.0
    error_rate = len(error_rows) / row_count if row_count else 0.0
    non_feasible_rate = len(non_feasible) / row_count if row_count else 0.0
    return {
        "strategy": strategy,
        "row_count": row_count,
        "successful_count": successful_count,
        "error_count": len(error_rows),
        "non_feasible_count": len(non_feasible),
        "feasible_rate": feasible_rate,
        "error_rate": error_rate,
        "non_feasible_rate": non_feasible_rate,
        "families_covered": sorted({str(row.get("family")) for row in rows if row.get("family")}),
        "family_count": len({str(row.get("family")) for row in rows if row.get("family")}),
        "cases_covered": sorted({str(row.get("benchmark_id")) for row in rows if row.get("benchmark_id")}),
        "case_count": len({str(row.get("benchmark_id")) for row in rows if row.get("benchmark_id")}),
        "tiers_covered": sorted({str(row.get("tier")) for row in rows if row.get("tier")}),
        "avg_gap_rel": sum(gap_values) / len(gap_values) if gap_values else None,
        "max_gap_rel": max(gap_values) if gap_values else None,
        "avg_elapsed_seconds": sum(elapsed_values) / len(elapsed_values) if elapsed_values else None,
        "total_elapsed_seconds": sum(elapsed_values) if elapsed_values else None,
        "avg_improvement_per_second": (
            sum(improvement_values) / len(improvement_values)
            if improvement_values
            else None
        ),
    }


def _default_candidate_sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    avg_gap = float("inf") if row.get("avg_gap_rel") is None else float(row["avg_gap_rel"])
    max_gap = float("inf") if row.get("max_gap_rel") is None else float(row["max_gap_rel"])
    avg_elapsed = (
        float("inf")
        if row.get("avg_elapsed_seconds") is None
        else float(row["avg_elapsed_seconds"])
    )
    return (
        -int(row.get("family_count", 0)),
        -int(row.get("case_count", 0)),
        -float(row.get("feasible_rate", 0.0)),
        float(row.get("error_rate", 0.0)),
        float(row.get("non_feasible_rate", 0.0)),
        avg_gap,
        max_gap,
        avg_elapsed,
        -float(row.get("avg_improvement_per_second") or 0.0),
        str(row.get("strategy") or ""),
    )


def _family_improvement_summary(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    summary: dict[str, dict[str, Any]] = {}
    for row in rows:
        if row.get("kind") != "strategy_run":
            continue
        family = str(row.get("family") or "unknown")
        bucket = summary.setdefault(
            family,
            {
                "rows_with_improvement": 0,
                "improvement_abs_sum": 0.0,
                "improvement_per_second_sum": 0.0,
                "avg_improvement_abs": None,
                "avg_improvement_per_second": None,
            },
        )
        improvement_abs = _float_or_none(row.get("improvement_abs"))
        improvement_per_second = _float_or_none(row.get("improvement_per_second"))
        if improvement_abs is None or improvement_per_second is None:
            continue
        bucket["rows_with_improvement"] += 1
        bucket["improvement_abs_sum"] += improvement_abs
        bucket["improvement_per_second_sum"] += improvement_per_second
    for bucket in summary.values():
        count = int(bucket["rows_with_improvement"])
        if count:
            bucket["avg_improvement_abs"] = bucket["improvement_abs_sum"] / count
            bucket["avg_improvement_per_second"] = bucket["improvement_per_second_sum"] / count
        del bucket["improvement_abs_sum"]
        del bucket["improvement_per_second_sum"]
    return summary


def _single_run_schema_gate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    required = ("benchmark_schema_version", "benchmark_id", "family", "strategy", "strategy_profile", "model_style", "kind", "status", "feasible", "runtime_s")
    issues = []
    for row in rows:
        missing = [field for field in required if row.get(field) is None]
        if missing:
            issues.append({"benchmark_id": row.get("benchmark_id"), "strategy": row.get("strategy"), "missing": missing})
    return {"status": "pass" if not issues else "fail", "issue_count": len(issues), "issues": issues}


def _single_run_feasible_gate(groups: list[dict[str, Any]]) -> dict[str, Any]:
    threshold = 0.5
    failures = [group for group in groups if float(group.get("feasible_rate") or 0.0) < threshold]
    return {"status": "pass" if not failures else "fail", "threshold": threshold, "failures": failures}


def _single_run_quality_gate(groups: list[dict[str, Any]]) -> dict[str, Any]:
    failures = [
        group
        for group in groups
        if group.get("gap_rel", {}).get("median") is not None and float(group["gap_rel"]["median"]) > 10.0
    ]
    return {"status": "pass" if not failures else "fail", "max_gap_rel": 10.0, "failures": failures}


def _single_run_runtime_gate(groups: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "status": "pass",
        "max_median_runtime_s": None,
        "reason": "no universal runtime threshold is configured for all benchmark families",
    }


def _rows_by_strategy(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row.get("strategy") or ""), []).append(row)
    return grouped


def _feedback_candidate(strategy: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    exact_rows = [row for row in rows if row.get("kind") == "exact_baseline"]
    feasible_rows = [row for row in rows if row.get("feasible") is True and row.get("status") != "error"]
    gaps = _numeric_values(feasible_rows, "gap_rel")
    elapsed = _numeric_values(rows, "elapsed_seconds")
    strategy_configs = [row.get("strategy_config") for row in rows if isinstance(row.get("strategy_config"), dict)]
    if exact_rows:
        recommendation_kind = "exact_api"
        resolved_config = {
            "api": "solve_milp",
            "strategy": strategy,
        }
    else:
        recommendation_kind = "strategy_config"
        resolved_config = {
            "strategy": strategy,
            "strategy_profile": rows[0].get("strategy_profile") if rows else None,
            "config": strategy_configs[0] if strategy_configs else None,
        }
    return {
        "strategy": strategy,
        "recommendation_kind": recommendation_kind,
        "resolved_config": resolved_config,
        "row_count": len(rows),
        "feasible_rate": _safe_ratio(len(feasible_rows), len(rows)),
        "error_count": sum(1 for row in rows if row.get("status") == "error"),
        "gap_rel": _distribution(gaps),
        "elapsed_seconds": _distribution(elapsed),
    }


def _feedback_sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    gap = row.get("gap_rel", {}).get("median")
    elapsed = row.get("elapsed_seconds", {}).get("median")
    return (
        0 if row.get("recommendation_kind") == "exact_api" else 1,
        -float(row.get("feasible_rate") or 0.0),
        int(row.get("error_count") or 0),
        float("inf") if gap is None else float(gap),
        float("inf") if elapsed is None else float(elapsed),
        str(row.get("strategy") or ""),
    )


def _numeric_values(rows: list[dict[str, Any]], field: str) -> list[float]:
    values = []
    for row in rows:
        value = _float_or_none(row.get(field))
        if value is not None:
            values.append(value)
    return values


def _distribution(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "min": None, "median": None, "max": None, "mean": None}
    ordered = sorted(values)
    return {
        "count": len(ordered),
        "min": ordered[0],
        "median": _median(ordered),
        "max": ordered[-1],
        "mean": sum(ordered) / len(ordered),
    }


def _median(ordered_values: list[float]) -> float:
    midpoint = len(ordered_values) // 2
    if len(ordered_values) % 2:
        return ordered_values[midpoint]
    return (ordered_values[midpoint - 1] + ordered_values[midpoint]) / 2.0


def _safe_ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def _load_run_rows(run_dir: Path) -> list[dict[str, Any]]:
    path = run_dir / "rows.jsonl"
    if not path.exists():
        path = run_dir / "results.jsonl"
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def write_results_csv(path: str | Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "kind",
        "benchmark_id",
        "family",
        "tier",
        "strategy",
        "strategy_profile",
        "budget_profile",
        "benchmark_schema_version",
        "thread_count",
        "parallel_matrix_enabled",
        "model_style",
        "solver_name",
        "status",
        "feasible",
        "objective",
        "best_cost",
        "reference_cost",
        "initial_cost",
        "improvement_abs",
        "improvement_rel",
        "improvement_per_second",
        "improvement_per_evaluation",
        "improvement_per_move",
        "raw_objective",
        "reference_objective",
        "gap_abs",
        "gap_rel",
        "runtime_s",
        "elapsed_seconds",
        "time_to_best_seconds",
        "time_to_first_feasible_seconds",
        "termination_reason",
        "effective_max_iterations",
        "effective_time_limit_s",
        "effective_population_size",
        "effective_exact_time_limit_s",
        "moves_attempted",
        "moves_accepted",
        "moves_improved",
        "evaluations",
        "delta_evaluations",
        "full_evaluations",
        "repairs_attempted",
        "repairs_succeeded",
        "moves_attempted_per_s",
        "moves_accepted_per_s",
        "evaluations_per_s",
        "delta_evaluations_per_s",
        "full_evaluations_per_s",
        "repairs_attempted_per_s",
        "repairs_succeeded_per_s",
        "construct_candidates_evaluated",
        "construct_best_improvements",
        "ga_scheduling_repair_count",
        "ga_scheduling_repair_success_count",
        "ga_infeasible_offspring_count",
        "ga_first_feasible_generation",
        "lns_applications",
        "sequence_graph_delta_count",
        "full_root_eval_delta_count",
        "tsp_two_opt_moves_evaluated",
        "tsp_two_opt_improvements",
        "tsp_repair_insertions",
        "tsp_preserved_edge_ratio",
        "qap_swap_delta_count",
        "qap_swap_improvement_count",
        "qap_repair_assignment_count",
        "qap_common_assignment_preservation_ratio",
        "dimension",
        "edge_weight_type",
    ]
    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def render_report(summary: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Modeling-Native Benchmark Run",
        "",
        f"- Run dir: `{summary['run_dir']}`",
        f"- Families: `{', '.join(summary['families'])}`",
        f"- Tiers: `{', '.join(summary['tiers'])}`",
        f"- Strategies: `{', '.join(summary['strategies'])}`",
        f"- Parallel matrix: `{summary.get('parallel_matrix_enabled', False)}`",
        f"- Thread counts: `{', '.join(str(value) for value in summary.get('parallel_thread_counts', [1]))}`",
        f"- Selected cases: {summary['selected_case_count']}",
        f"- Executed cases: {summary['executed_case_count']}",
        f"- Runs: {summary['strategy_run_count']}",
        f"- Strategy rows: {summary.get('strategy_row_count', 0)}",
        f"- Exact baseline rows: {summary.get('exact_baseline_row_count', 0)}",
        f"- Successful runs: {summary['successful_run_count']}",
        f"- Non-feasible runs: {summary['non_feasible_run_count']}",
        f"- Error runs: {summary['error_run_count']}",
        "",
        "## Effective Strategies",
        "",
        "| Family | Strategies |",
        "| --- | --- |",
    ]
    for family, strategies in sorted(summary.get("family_strategy_plan", {}).items()):
        strategy_text = ", ".join(f"`{strategy}`" for strategy in strategies)
        lines.append(f"| `{family}` | {strategy_text} |")
    if summary.get("strategy_substitutions"):
        lines.extend(["", "Strategy substitutions:", ""])
        for item in summary["strategy_substitutions"]:
            requested = ", ".join(item.get("requested", []))
            effective = ", ".join(item.get("effective", []))
            lines.append(
                f"- `{item.get('family')}`: `{requested}` -> `{effective}` ({item.get('reason')})"
            )
    lines.extend(
        [
            "",
            "## Family Budgets",
            "",
            "| Family | Tier | Budget profile | Iterations | Seconds | Population | Trace | Exact seconds |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for family, tier_budgets in sorted(summary.get("family_budgets", {}).items()):
        for tier, budget in sorted(tier_budgets.items()):
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{family}`",
                        f"`{tier}`",
                        f"`{budget.get('profile', '')}`",
                        _fmt(budget.get("max_iterations")),
                        _fmt(budget.get("time_limit_s")),
                        _fmt(budget.get("population_size")),
                        _fmt(budget.get("trace_limit")),
                        _fmt(budget.get("exact_time_limit_s")),
                    ]
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "## Strategy Profiles",
            "",
            "| Profile | Rows |",
            "| --- | ---: |",
        ]
    )
    for profile, count in sorted(summary.get("profile_counts", {}).items()):
        lines.append(f"| `{profile}` | {count} |")
    lines.extend(
        [
            "",
            "## Search Efficiency",
            "",
            "| Family | Rows with improvement | Avg improvement | Avg improvement/s |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for family, item in sorted(summary.get("family_improvement_summary", {}).items()):
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{family}`",
                    _fmt(item.get("rows_with_improvement")),
                    _fmt(item.get("avg_improvement_abs")),
                    _fmt(item.get("avg_improvement_per_second")),
                ]
            )
                + " |"
        )
    gates = summary.get("regression_gates", {})
    lines.extend(
        [
            "",
            "## Regression Gates",
            "",
            f"- Overall status: `{gates.get('overall_status', '')}`",
            "",
            "| Gate | Status | Detail |",
            "| --- | --- | --- |",
        ]
    )
    for gate_name, gate in sorted(gates.get("checks", {}).items()):
        detail = gate.get("reason")
        if detail is None:
            if "issue_count" in gate:
                detail = f"issues={gate.get('issue_count')}"
            elif "threshold" in gate:
                detail = f"threshold={gate.get('threshold')}, failures={len(gate.get('failures', []))}"
            elif "max_gap_rel" in gate:
                detail = f"max_gap_rel={gate.get('max_gap_rel')}, failures={len(gate.get('failures', []))}"
            else:
                detail = ""
        lines.append(f"| `{gate_name}` | `{gate.get('status')}` | {detail} |")
    feedback = summary.get("strategy_feedback", {})
    lines.extend(
        [
            "",
            "## Strategy Feedback",
            "",
            f"- Override policy: {feedback.get('explicit_user_strategy_override_policy', '')}",
            f"- Reference policy: {feedback.get('reference_policy', '')}",
            "",
            "| Family | Style | Recommendation kind | Recommendation | Feasible % | Median gap % | Median seconds |",
            "| --- | --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for group in feedback.get("groups", []):
        recommendation = group.get("recommendation") or {}
        resolved = recommendation.get("resolved_config") or {}
        if recommendation.get("recommendation_kind") == "exact_api":
            recommendation_text = resolved.get("api") or ""
        else:
            recommendation_text = recommendation.get("strategy") or ""
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{group.get('family')}`",
                    f"`{group.get('model_style') or ''}`",
                    f"`{recommendation.get('recommendation_kind') or ''}`",
                    f"`{recommendation_text}`",
                    _fmt_pct(recommendation.get("feasible_rate")),
                    _fmt_pct((recommendation.get("gap_rel") or {}).get("median")),
                    _fmt((recommendation.get("elapsed_seconds") or {}).get("median")),
                ]
            )
            + " |"
        )
    if summary.get("parallel_matrix_enabled"):
        matrix = summary.get("parallel_matrix", {})
        lines.extend(
            [
                "",
                "## Parallel Matrix",
                "",
                f"- Thread counts: `{', '.join(str(value) for value in matrix.get('thread_counts', []))}`",
                "",
                "| Case | Strategy | Profile | Style | Kind | Threads | Objective | Gap % | Seconds | Speedup | Efficiency | Quality delta | Throughput speedup |",
                "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for group in matrix.get("groups", []):
            for row in group.get("rows", []):
                lines.append(
                    "| "
                    + " | ".join(
                        [
                            f"`{group.get('benchmark_id')}`",
                            f"`{group.get('strategy')}`",
                            f"`{group.get('strategy_profile')}`",
                            f"`{group.get('model_style')}`",
                            f"`{group.get('kind')}`",
                            _fmt(row.get("thread_count")),
                            _fmt(row.get("objective")),
                            _fmt_pct(row.get("gap_rel")),
                            _fmt(row.get("elapsed_seconds")),
                            _fmt(row.get("speedup")),
                            _fmt(row.get("efficiency")),
                            _fmt(row.get("quality_delta_vs_1_thread")),
                            _fmt(row.get("throughput_speedup")),
                        ]
                    )
                    + " |"
                )
    if summary.get("default_candidate_matrix_enabled"):
        matrix = summary.get("default_candidate_matrix", {})
        lines.extend(
            [
                "",
                "## Default Strategy Candidate Matrix",
                "",
                f"- Selection policy: `{matrix.get('selection_policy', '')}`",
                f"- Recommended strategy: `{matrix.get('recommended_strategy') or ''}`",
                "",
                "| Rank | Strategy | Recommended | Rows | Families | Cases | Feasible % | Errors | Non-feasible | Avg gap % | Max gap % | Avg seconds | Avg improvement/s |",
                "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in matrix.get("ranked_strategies", []):
            lines.append(
                "| "
                + " | ".join(
                    [
                        _fmt(row.get("rank")),
                        f"`{row.get('strategy')}`",
                        "yes" if row.get("recommended") else "",
                        _fmt(row.get("row_count")),
                        _fmt(row.get("family_count")),
                        _fmt(row.get("case_count")),
                        _fmt_pct(row.get("feasible_rate")),
                        _fmt(row.get("error_count")),
                        _fmt(row.get("non_feasible_count")),
                        _fmt_pct(row.get("avg_gap_rel")),
                        _fmt_pct(row.get("max_gap_rel")),
                        _fmt(row.get("avg_elapsed_seconds")),
                        _fmt(row.get("avg_improvement_per_second")),
                    ]
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "## Best By Case",
            "",
            "| Case | Best route | Profile | Style | Kind | Objective | Reference | Gap | Gap % | Seconds |",
            "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for benchmark_id, row in summary["best_by_case"].items():
        gap_rel = row.get("gap_rel")
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{benchmark_id}`",
                    f"`{row['strategy']}`",
                    f"`{row.get('strategy_profile') or ''}`",
                    f"`{row.get('model_style') or ''}`",
                    f"`{row.get('kind') or ''}`",
                    _fmt(row.get("objective")),
                    _fmt(row.get("reference_objective")),
                    _fmt(row.get("gap_abs")),
                    _fmt_pct(gap_rel),
                    _fmt(row.get("elapsed_seconds")),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Runs",
            "",
            "| Case | Route | Profile | Budget profile | Style | Kind | Status | Objective | Raw objective | Gap % | Seconds | Metadata highlights |",
            "| --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in rows:
        metadata = row.get("metadata", {})
        highlights = metadata_highlights(metadata) if isinstance(metadata, dict) else []
        error = row.get("error")
        if error:
            highlights.append(f"error={error['type']}")
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['benchmark_id']}`",
                    f"`{row['strategy']}`",
                    f"`{row.get('strategy_profile') or ''}`",
                    f"`{row.get('budget_profile') or ''}`",
                    f"`{row.get('model_style') or ''}`",
                    f"`{row.get('kind') or ''}`",
                    str(row.get("status")),
                    _fmt(row.get("objective")),
                    _fmt(row.get("raw_objective")),
                    _fmt_pct(row.get("gap_rel")),
                    _fmt(row.get("elapsed_seconds")),
                    ", ".join(highlights) if highlights else "",
                ]
            )
            + " |"
        )

    if summary["skipped_cases"]:
        lines.extend(["", "## Skipped Cases", "", "| Case | Family | Reason |", "| --- | --- | --- |"])
        for row in summary["skipped_cases"]:
            lines.append(f"| `{row['benchmark_id']}` | `{row['family']}` | {row['reason']} |")
    return "\n".join(lines) + "\n"


def _fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def _fmt_pct(value: Any) -> str:
    if value is None:
        return ""
    return f"{float(value) * 100:.3f}%"


if __name__ == "__main__":
    raise SystemExit(main())
