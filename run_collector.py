"""Benchmark run result collector for the scoring pipeline.

Wraps an optagent solve() call and extracts all fields needed by scoring.py
into a BenchmarkRun JSON structure. Also writes incumbent_trace.json artifact.

Usage:
    from benchmarks.run_collector import BenchmarkRunCollector

    collector = BenchmarkRunCollector(
        benchmark_group="routing",
        benchmark_id="tsp_20",
        strategy="ga",
        reference_cost=100.0,
    )
    result = collector.run(program, strategy=GaConfig(), time_limit_s=30, seed=42)
    collector.save(output_dir="results/routing/ga/")
"""
from __future__ import annotations

import json
import os
import platform
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from optagent.api import solve
from optagent.solution.models import UnifiedSolution
from optagent.strategy import StrategyConfig


def _git_commit() -> str:
    """Get current git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5,
            cwd=str(REPO_ROOT),
        )
        return result.stdout.strip()[:12] if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def _environment() -> dict[str, str]:
    """Collect environment info."""
    return {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "arch": platform.machine(),
    }


@dataclass
class BenchmarkRunCollector:
    """Collects a single benchmark run's data for the scoring pipeline."""

    # Identity
    benchmark_group: str
    benchmark_id: str
    strategy: str
    strategy_profile: str = "default"

    # Reference for D1/D2 scoring
    reference_cost: float | None = None

    # Run configuration
    family: str = ""
    tier: str = "standard"

    # Internal state (set after run)
    _result: UnifiedSolution | None = field(default=None, repr=False)
    _run_data: dict[str, Any] = field(default_factory=dict, repr=False)
    _run_id: str = ""
    _seed: int = 0
    _time_limit_s: float = 30.0
    _strategy_config: dict[str, Any] = field(default_factory=dict, repr=False)

    def run(
        self,
        program: Any,
        *,
        strategy: StrategyConfig | str | None = None,
        time_limit_s: float = 30.0,
        seed: int = 0,
        log_level: str = "off",
        **solve_kwargs: Any,
    ) -> UnifiedSolution:
        """Run solve() and collect all scoring-relevant data."""
        self._seed = seed
        self._time_limit_s = time_limit_s

        # Capture strategy config for output
        if strategy is not None and hasattr(strategy, '__dataclass_fields__'):
            from dataclasses import asdict
            self._strategy_config = asdict(strategy)
        elif isinstance(strategy, str):
            self._strategy_config = {"strategy_name": strategy}

        # Run solve
        start = time.time()
        result = solve(
            program,
            strategy=strategy,
            time_limit_s=time_limit_s,
            seed=seed,
            log_level=log_level,
            **solve_kwargs,
        )
        wall_time = time.time() - start

        self._result = result
        self._run_id = f"{self.benchmark_group}-{self.benchmark_id}-{self.strategy}-s{seed}-{int(time.time())}"

        # Build run data
        diag = result.diagnostics or {}
        objective = result.objective_value

        # Extract metrics
        metrics: dict[str, Any] = {
            "status": "success" if result.feasible is not None else "error",
            "feasible": result.feasible,
            "objective": objective,
            "best_cost": objective,
            "runtime_ms": wall_time * 1000,
            "iterations": int(diag.get("total_iterations", 0) or diag.get("ga_generation_count", 0) or 0),
            "time_to_best_ms": float(diag.get("time_to_best_s", 0) or 0) * 1000,
            "evaluations_per_s": _safe_div(
                int(diag.get("loop_candidates_evaluated", 0) or 0) +
                int(diag.get("construct_candidates_evaluated", 0) or 0),
                wall_time,
            ),
        }

        # Include reference cost if provided
        if self.reference_cost is not None:
            metrics["reference_cost"] = self.reference_cost
            metrics["best_known_solution"] = self.reference_cost
            if objective is not None and self.reference_cost != 0:
                metrics["gap_rel"] = (objective - self.reference_cost) / abs(self.reference_cost)

        # Time budget
        metrics["time_budget_s"] = time_limit_s

        # Operator diagnostics: scoring-relevant fields
        operator_diagnostics: dict[str, Any] = {}
        scoring_fields = [
            "incumbent_trace_json",
            "time_to_best_s",
            "diversity_at_termination",
            "unimproved_iterations",
            "total_iterations",
            "loop_candidates_evaluated",
            "construct_candidates_evaluated",
            "wall_time_seconds",
            "termination_reason",
            "termination_policy",
            "restarts",
            "attempted_moves",
            "accepted_moves",
            "improved_moves",
        ]
        for field_name in scoring_fields:
            if field_name in diag:
                operator_diagnostics[field_name] = diag[field_name]

        # Also include GA-specific diagnostics
        ga_fields = [
            "ga_generation_count", "ga_offspring_evaluated",
            "ga_crossover_count", "ga_mutation_count",
            "ga_best_generation", "ga_offspring_generated",
        ]
        for field_name in ga_fields:
            if field_name in diag:
                operator_diagnostics[field_name] = diag[field_name]

        commit = _git_commit()
        self._run_data = {
            "schema_version": 2,
            "run_id": self._run_id,
            "benchmark_group": self.benchmark_group,
            "benchmark_id": self.benchmark_id,
            "family": self.family or self.benchmark_group,
            "tier": self.tier,
            "strategy": self.strategy,
            "strategy_profile": self.strategy_profile,
            "strategy_config": self._strategy_config,
            "seed": seed,
            "optagent": {
                "version": "0.2.0",
                "commit": commit,
                "commit_url": f"https://github.com/Dongbox/optagent/commit/{commit}",
                "wheel_sha256": "",
            },
            "benchmarks": {
                "commit": commit,
                "commit_url": f"https://github.com/Dongbox/optagent/commit/{commit}",
            },
            "environment": _environment(),
            "metrics": metrics,
            "operator_diagnostics": operator_diagnostics,
            "artifacts": {},
            "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

        return result

    def save(self, output_dir: str | Path) -> Path:
        """Save run data and incumbent trace to output directory.

        Returns the path to the run summary JSON.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save run summary
        summary_path = output_dir / f"{self._run_id}.json"
        summary_path.write_text(json.dumps(self._run_data, indent=2, ensure_ascii=False) + "\n")

        # Save incumbent_trace.json artifact if available
        diag = self._run_data.get("operator_diagnostics", {})
        trace_json_str = diag.get("incumbent_trace_json")
        if trace_json_str:
            trace_path = output_dir / f"{self._run_id}_incumbent_trace.json"
            try:
                events = json.loads(trace_json_str)
                trace_data = {
                    "time_budget_s": self._time_limit_s,
                    "reference_cost": self.reference_cost,
                    "events": events,
                }
                # Compute primal integral and anytime score here
                if self.reference_cost and self.reference_cost != 0 and events:
                    from benchmarks.scoring import compute_primal_integral, IncumbentEvent, score_anytime
                    trace_events = [IncumbentEvent(e["elapsed_s"], e["objective"]) for e in events]
                    pi = compute_primal_integral(trace_events, self.reference_cost, self._time_limit_s)
                    anytime_score, _ = score_anytime(
                        trace_events, self.reference_cost, self._time_limit_s,
                        self.benchmark_group, self._run_data["metrics"].get("feasible", False),
                    )
                    trace_data["primal_integral"] = pi
                    trace_data["anytime_score"] = anytime_score

                trace_path.write_text(json.dumps(trace_data, indent=2, ensure_ascii=False) + "\n")
                # Record artifact path (relative)
                self._run_data["artifacts"]["incumbent_trace"] = str(trace_path.relative_to(output_dir.parent.parent))
            except (json.JSONDecodeError, ImportError, Exception):
                pass

        # Re-save summary with updated artifacts
        summary_path.write_text(json.dumps(self._run_data, indent=2, ensure_ascii=False) + "\n")

        return summary_path

    @property
    def run_data(self) -> dict[str, Any]:
        """Access the raw run data dict."""
        return self._run_data

    @property
    def run_id(self) -> str:
        return self._run_id


def _safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator > 0 else 0.0
