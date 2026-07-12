from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
from typing import Any, Callable, Sequence

from benchmarks.authority import (
    AuthorityInputs,
    assess_authority,
    assess_capabilities,
    case_lifecycle_inventory,
    iter_run_coordinates,
    make_run_key,
)
from benchmarks.cases.registry import benchmark_case_objects
from benchmarks.paths import REPOSITORY_ROOT
from benchmarks.presentation.common import StrategyBudgetRequest, resolve_family_tier_budget


SCHEMA_VERSION = 1
REPO_ROOT = REPOSITORY_ROOT
BENCHMARKS_ROOT = REPOSITORY_ROOT


@dataclass(frozen=True)
class PlannedRun:
    benchmark_id: str
    family: str
    tier: str
    model_style: str
    solve_route: str
    strategy: str
    seed: int
    max_iterations: int
    time_limit_s: float
    population_size: int
    trace_limit: int
    thread_count: int

    @property
    def run_key(self) -> str:
        return make_run_key(
            benchmark_id=self.benchmark_id,
            model_style=self.model_style,
            solve_route=self.solve_route,
            strategy=self.strategy,
            seed=self.seed,
            thread_count=self.thread_count,
        )


def planned_runs() -> tuple[PlannedRun, ...]:
    runs: list[PlannedRun] = []
    for coordinate in iter_run_coordinates():
        budget = resolve_family_tier_budget(
            family=coordinate.family,
            tier=coordinate.tier,
            request=StrategyBudgetRequest(seed=coordinate.seed, thread_count=coordinate.thread_count),
        )
        runs.append(
            PlannedRun(
                benchmark_id=coordinate.benchmark_id,
                family=coordinate.family,
                tier=coordinate.tier,
                model_style=coordinate.model_style,
                solve_route=coordinate.solve_route,
                strategy=coordinate.strategy,
                seed=coordinate.seed,
                max_iterations=budget.max_iterations,
                time_limit_s=budget.exact_time_limit_s or budget.time_limit_s,
                population_size=budget.population_size,
                trace_limit=budget.trace_limit,
                thread_count=budget.thread_count,
            )
        )
    return tuple(runs)


def build_run_command(python_executable: str, run: PlannedRun, *, allow_download: bool) -> list[str]:
    command = [
        python_executable,
        str(REPO_ROOT / "benchmark.py"),
        "run",
        "--case",
        run.benchmark_id,
        "--strategy",
        run.strategy,
        "--model-style",
        run.model_style,
        "--seed",
        str(run.seed),
        "--max-iterations",
        str(run.max_iterations),
        "--time-limit-s",
        str(run.time_limit_s),
        "--population-size",
        str(run.population_size),
        "--trace-limit",
        str(run.trace_limit),
        "--thread-count",
        str(run.thread_count),
    ]
    if not allow_download:
        command.append("--no-download")
    return command


def run_baseline(
    *,
    output_dir: Path,
    wheel_path: Path,
    bootstrap_python: str,
    allow_download: bool,
    memory_limit_mb: int,
    optagent_commit: str,
) -> dict[str, Any]:
    output_dir = output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"authoritative baseline output directory is not empty: {output_dir}")
    inputs = AuthorityInputs(
        optagent_commit=optagent_commit,
        benchmarks_commit=_git_output(BENCHMARKS_ROOT, "rev-parse", "HEAD"),
        wheel_sha256=f"sha256:{_sha256(wheel_path)}",
        optagent_dirty=False,
        benchmarks_dirty=bool(_git_output(BENCHMARKS_ROOT, "status", "--porcelain")),
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="optagent-authority-") as temp_dir:
        python_executable = _install_wheel_environment(
            bootstrap_python=bootstrap_python,
            wheel_path=wheel_path,
            environment_dir=Path(temp_dir),
        )
        installed_runtime = _installed_runtime_identity(python_executable)
        rows: list[dict[str, Any]] = []
        for run in planned_runs():
            rows.append(
                _run_child(
                    run,
                    python_executable=python_executable,
                    allow_download=allow_download,
                    memory_limit_mb=memory_limit_mb,
                    installed_runtime=installed_runtime,
                )
            )

        data_checksums = _data_checksums()
        assessment = assess_authority(inputs, rows, evidence_checksums=data_checksums)
        capability_assessment = assess_capabilities(rows)
        rows_path = output_dir / "rows.jsonl"
        rows_path.write_text(
            "".join(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n" for row in rows),
            encoding="utf-8",
        )
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "kind": "optagent_authoritative_baseline",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "authority_status": assessment.status,
        "authority_reasons": list(assessment.reasons),
        "capability_assessment": capability_assessment,
        "provenance": asdict(inputs),
        "environment": {
            "python": platform.python_version(),
            "bootstrap_python": str(Path(bootstrap_python).resolve()),
            "installed_runtime": installed_runtime,
            "platform": platform.platform(),
            "platform_coordinate": _platform_coordinate(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "cpu_count": os.cpu_count(),
        },
        "protocol": {
            "process_isolation": True,
            "hard_timeout_grace_s": 15.0,
            "memory_limit_requested_mb": memory_limit_mb,
            "memory_limit_enforced": _memory_limiter(memory_limit_mb) is not None,
            "heuristic_seed_count": 3,
            "thread_count": 1,
            "independent_solution_verification_required": True,
        },
        "planned_run_count": len(planned_runs()),
        "completed_row_count": len(rows),
        "case_lifecycle": case_lifecycle_inventory(),
        "data_checksums": data_checksums,
        "artifacts": {"rows.jsonl": f"sha256:{_sha256(rows_path)}"},
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=True, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def _install_wheel_environment(*, bootstrap_python: str, wheel_path: Path, environment_dir: Path) -> str:
    subprocess.run(
        [bootstrap_python, "-m", "venv", str(environment_dir)],
        check=True,
        cwd=REPO_ROOT,
    )
    python_executable = environment_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    subprocess.run(
        [str(python_executable), "-m", "pip", "install", str(wheel_path.resolve())],
        check=True,
        cwd=REPO_ROOT,
    )
    return str(python_executable)


def _installed_runtime_identity(python_executable: str) -> dict[str, Any]:
    script = """
import importlib
import importlib.metadata
import json
from pathlib import Path
import re

import optagent

native = importlib.import_module("_optagent_native")
config_text = (Path(native.__file__).parent / "include" / "highs" / "HConfig.h").read_text(encoding="utf-8")

def macro(name):
    match = re.search(rf"^#define {name} (\\d+)$", config_text, re.MULTILINE)
    return match.group(1) if match else ""

highs_version = ".".join(
    macro(name) for name in ("HIGHS_VERSION_MAJOR", "HIGHS_VERSION_MINOR", "HIGHS_VERSION_PATCH")
)
print(json.dumps({
    "version": importlib.metadata.version("optagent"),
    "package_file": optagent.__file__,
    "native_file": native.__file__,
    "embedded_highs_version": highs_version,
}, sort_keys=True))
"""
    completed = subprocess.run(
        [python_executable, "-c", script],
        cwd=REPO_ROOT,
        env={**os.environ, "OPTAGENT_BENCHMARK_USE_INSTALLED": "1"},
        text=True,
        capture_output=True,
        check=True,
    )
    return dict(json.loads(completed.stdout))


def _run_child(
    run: PlannedRun,
    *,
    python_executable: str,
    allow_download: bool,
    memory_limit_mb: int,
    installed_runtime: dict[str, Any],
) -> dict[str, Any]:
    command = build_run_command(python_executable, run, allow_download=allow_download)
    env = dict(os.environ)
    env["OPTAGENT_BENCHMARK_USE_INSTALLED"] = "1"
    timeout_s = max(1.0, run.time_limit_s) + 15.0
    try:
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout_s,
            check=False,
            preexec_fn=_memory_limiter(memory_limit_mb),
        )
    except subprocess.TimeoutExpired as exc:
        return _failed_row(
            run,
            "hard_timeout",
            f"child exceeded {timeout_s:.1f}s",
            installed_runtime=installed_runtime,
            stderr=exc.stderr,
        )
    if completed.returncode != 0:
        return _failed_row(
            run,
            "process_exit",
            f"child exited with code {completed.returncode}",
            installed_runtime=installed_runtime,
            stderr=completed.stderr,
        )
    try:
        payload = json.loads(completed.stdout)
        row = dict(payload[0])
    except (json.JSONDecodeError, IndexError, TypeError, ValueError) as exc:
        return _failed_row(
            run,
            "invalid_child_output",
            str(exc),
            installed_runtime=installed_runtime,
            stderr=completed.stderr,
        )
    row["run_key"] = run.run_key
    row["solve_route"] = run.solve_route
    row["platform"] = _platform_coordinate()
    row.update(_backend_identity(run, installed_runtime))
    row["seed"] = run.seed
    row["thread_count"] = run.thread_count
    row["effective_budget"] = {
        "max_iterations": run.max_iterations,
        "time_limit_s": run.time_limit_s,
        "population_size": run.population_size,
        "trace_limit": run.trace_limit,
    }
    return row


def _failed_row(
    run: PlannedRun,
    failure_type: str,
    message: str,
    *,
    installed_runtime: dict[str, Any],
    stderr: Any = None,
) -> dict[str, Any]:
    return {
        "run_key": run.run_key,
        "benchmark_id": run.benchmark_id,
        "family": run.family,
        "tier": run.tier,
        "model_style": run.model_style,
        "solve_route": run.solve_route,
        "platform": _platform_coordinate(),
        "strategy": run.strategy,
        **_backend_identity(run, installed_runtime),
        "seed": run.seed,
        "thread_count": run.thread_count,
        "status": "error",
        "feasible": False,
        "verification_status": "not_run",
        "verification_passed": False,
        "error": {
            "type": failure_type,
            "message": message,
            "stderr": str(stderr or "")[-4000:],
        },
    }


def _memory_limiter(memory_limit_mb: int) -> Callable[[], None] | None:
    if not sys.platform.startswith("linux") or memory_limit_mb <= 0:
        return None

    def limit() -> None:
        import resource

        byte_limit = memory_limit_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (byte_limit, byte_limit))

    return limit


def _data_checksums() -> dict[str, str]:
    checksums: dict[str, str] = {}
    release_ids = {coordinate.benchmark_id for coordinate in iter_run_coordinates()}
    for case in benchmark_case_objects():
        if case.benchmark_id not in release_ids:
            continue
        checksums[f"{case.benchmark_id}:reference"] = f"sha256:{_sha256_json(dict(case.reference))}"
        for key in ("data_path", "raw_path", "solution_raw_path"):
            raw_path = case.data.get(key)
            if not raw_path:
                continue
            path = Path(str(raw_path))
            if path.exists():
                checksums[f"{case.benchmark_id}:instance:{key}"] = f"sha256:{_sha256(path)}"
    return dict(sorted(checksums.items()))


def _sha256_json(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _backend_identity(run: PlannedRun, installed_runtime: dict[str, Any]) -> dict[str, str]:
    if run.solve_route == "embedded_highs":
        return {
            "backend_name": "highs",
            "backend_version": str(installed_runtime.get("embedded_highs_version") or ""),
        }
    return {
        "backend_name": "optagent_native_search",
        "backend_version": str(installed_runtime.get("version") or "unknown"),
    }


def _platform_coordinate() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    if system == "darwin":
        system = "macos"
    if machine in {"amd64", "x64"}:
        machine = "x86_64"
    return f"{system}_{machine}"


def _git_output(cwd: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate an OptAgent authoritative release-gate baseline.")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--wheel", required=True, help="Exact OptAgent wheel to install in an isolated child environment."
    )
    parser.add_argument("--optagent-commit", required=True, help="Commit SHA used to build the OptAgent wheel.")
    parser.add_argument(
        "--python-executable", default=sys.executable, help="Python used to create the isolated wheel environment."
    )
    parser.add_argument("--allow-download", action="store_true")
    parser.add_argument("--memory-limit-mb", type=int, default=4096)
    parser.add_argument("--require-authoritative", action="store_true")
    parser.add_argument(
        "--plan-only",
        action="store_true",
        help="Validate and print the frozen run plan without creating environments or authority evidence.",
    )
    args = parser.parse_args(argv)
    wheel_path = Path(args.wheel).resolve()
    if not wheel_path.is_file():
        parser.error(f"wheel not found: {wheel_path}")
    if args.plan_only:
        print(
            json.dumps(
                {
                    "kind": "optagent_authority_plan",
                    "authoritative": False,
                    "optagent_commit": args.optagent_commit,
                    "wheel": str(wheel_path),
                    "planned_run_count": len(planned_runs()),
                    "runs": [asdict(run) for run in planned_runs()],
                },
                indent=2,
                ensure_ascii=True,
                sort_keys=True,
            )
        )
        return 0
    manifest = run_baseline(
        output_dir=Path(args.output_dir),
        wheel_path=wheel_path,
        bootstrap_python=args.python_executable,
        allow_download=args.allow_download,
        memory_limit_mb=args.memory_limit_mb,
        optagent_commit=args.optagent_commit,
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=True, sort_keys=True))
    if args.require_authoritative and manifest["authority_status"] != "authoritative":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
