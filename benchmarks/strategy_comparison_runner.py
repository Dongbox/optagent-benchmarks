from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import tempfile
from typing import Any, Literal

from benchmarks.artifact_io import sha256_file, write_json
from benchmarks.comparison_artifacts import publish_run_artifact
from benchmarks.comparison_protocol import ComparisonProtocol
from benchmarks.paths import REPOSITORY_ROOT


REPO_ROOT = REPOSITORY_ROOT
BENCHMARKS_ROOT = REPOSITORY_ROOT
RunRole = Literal["baseline", "challenger"]


@dataclass(frozen=True)
class PlannedProtocolRun:
    family: str
    model_style: str
    benchmark_id: str
    seed: int

    @property
    def coordinate(self) -> str:
        return f"{self.family}|{self.model_style}|{self.benchmark_id}|seed={self.seed}"


@dataclass(frozen=True)
class PlannedExecution:
    coordinate: str
    role: RunRole
    run: PlannedProtocolRun
    pair_index: int


def planned_protocol_runs(protocol: ComparisonProtocol) -> tuple[PlannedProtocolRun, ...]:
    return tuple(
        PlannedProtocolRun(profile.family, profile.model_style, case_id, seed)
        for profile in protocol.profiles
        for case_id in profile.case_ids
        for seed in protocol.seeds
    )


def interleaved_execution_plan(protocol: ComparisonProtocol) -> tuple[PlannedExecution, ...]:
    executions = []
    for index, run in enumerate(planned_protocol_runs(protocol)):
        roles: tuple[RunRole, RunRole] = ("baseline", "challenger") if index % 2 == 0 else ("challenger", "baseline")
        executions.extend(PlannedExecution(run.coordinate, role, run, index) for role in roles)
    return tuple(executions)


def build_child_command(
    python_executable: str,
    run: PlannedProtocolRun,
    protocol: ComparisonProtocol,
    *,
    allow_download: bool,
) -> list[str]:
    command = [
        python_executable,
        str(REPO_ROOT / "benchmark.py"),
        "run",
        "--case",
        run.benchmark_id,
        "--strategy",
        protocol.strategy,
        "--model-style",
        run.model_style,
        "--seed",
        str(run.seed),
        "--max-iterations",
        str(protocol.max_iterations),
        "--time-limit-s",
        str(protocol.wall_time_s),
        "--population-size",
        str(protocol.population_size),
        "--trace-limit",
        str(protocol.trace_limit),
        "--thread-count",
        str(protocol.thread_count),
    ]
    if not allow_download:
        command.append("--no-download")
    return command


def run_protocol_pair(
    *,
    protocol: ComparisonProtocol,
    baseline_wheel: str | Path,
    challenger_wheel: str | Path,
    output_dir: str | Path,
    bootstrap_python: str,
    allow_download: bool,
    baseline_commit: str = "unknown",
    challenger_commit: str = "unknown",
) -> dict[str, Any]:
    from benchmarks.strategy_comparison import compare_run_artifacts

    out = Path(output_dir).resolve()
    bootstrap_python = str(Path(bootstrap_python).resolve())
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"strategy comparison output directory is not empty: {out}")
    out.mkdir(parents=True, exist_ok=True)
    baseline_wheel_path = Path(baseline_wheel).resolve()
    challenger_wheel_path = Path(challenger_wheel).resolve()
    with tempfile.TemporaryDirectory(prefix="optagent-ga-comparison-") as temp_dir:
        temp_root = Path(temp_dir)
        python_by_role = {
            "baseline": _install_wheel_environment(bootstrap_python, baseline_wheel_path, temp_root / "baseline"),
            "challenger": _install_wheel_environment(bootstrap_python, challenger_wheel_path, temp_root / "challenger"),
        }
        runtime_by_role = {
            role: _runtime_identity(python_executable) for role, python_executable in python_by_role.items()
        }
        rows: dict[str, list[dict[str, Any]]] = {"baseline": [], "challenger": []}
        execution_log = []
        for execution in interleaved_execution_plan(protocol):
            row = _run_child(
                execution.run,
                protocol,
                python_executable=python_by_role[execution.role],
                allow_download=allow_download,
                runtime=runtime_by_role[execution.role],
            )
            rows[execution.role].append(row)
            execution_log.append(
                {
                    "pair_index": execution.pair_index,
                    "coordinate": execution.coordinate,
                    "role": execution.role,
                    "status": row.get("status"),
                }
            )

        benchmark_commit = _git_output(BENCHMARKS_ROOT, "rev-parse", "HEAD")
        common_provenance = {
            "benchmarks_commit": benchmark_commit,
            "benchmarks_dirty_before_execution": bool(_git_output(BENCHMARKS_ROOT, "status", "--porcelain")),
            "platform": _platform_coordinate(),
        }
        publish_run_artifact(
            rows["baseline"],
            out / "baseline",
            protocol=protocol,
            role="baseline",
            provenance={
                **common_provenance,
                "optagent_commit": baseline_commit,
                "wheel_sha256": sha256_file(baseline_wheel_path),
                "installed_runtime": runtime_by_role["baseline"],
            },
        )
        publish_run_artifact(
            rows["challenger"],
            out / "challenger",
            protocol=protocol,
            role="challenger",
            provenance={
                **common_provenance,
                "optagent_commit": challenger_commit,
                "wheel_sha256": sha256_file(challenger_wheel_path),
                "installed_runtime": runtime_by_role["challenger"],
            },
        )
    write_json(
        out / "execution_plan.json",
        {
            "protocol_id": protocol.protocol_id,
            "protocol_checksum": protocol.checksum,
            "execution_order": protocol.execution_order,
            "executions": execution_log,
        },
    )
    return compare_run_artifacts(out / "baseline", out / "challenger", out / "comparison")


def _run_child(
    run: PlannedProtocolRun,
    protocol: ComparisonProtocol,
    *,
    python_executable: str,
    allow_download: bool,
    runtime: dict[str, Any],
) -> dict[str, Any]:
    command = build_child_command(python_executable, run, protocol, allow_download=allow_download)
    env = {**os.environ, "OPTAGENT_BENCHMARK_USE_INSTALLED": "1"}
    timeout_s = protocol.wall_time_s + 15.0
    try:
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return _failure_row(run, protocol, "hard_timeout", f"child exceeded {timeout_s:.1f}s", str(exc.stderr or ""))
    if completed.returncode != 0:
        return _failure_row(
            run,
            protocol,
            "process_exit",
            f"child exited with code {completed.returncode}",
            completed.stderr,
        )
    try:
        payload = json.loads(completed.stdout)
        row = dict(payload[0])
    except (json.JSONDecodeError, IndexError, TypeError, ValueError) as exc:
        return _failure_row(run, protocol, "invalid_child_output", str(exc), completed.stderr)
    row.update(
        {
            "benchmark_id": run.benchmark_id,
            "family": run.family,
            "model_style": run.model_style,
            "strategy": protocol.strategy,
            "solve_route": protocol.solve_route,
            "platform": _platform_coordinate(),
            "seed": run.seed,
            "thread_count": protocol.thread_count,
            "backend_name": "optagent_native_search",
            "backend_version": str(runtime.get("version") or "unknown"),
            "effective_budget": {
                "max_iterations": protocol.max_iterations,
                "time_limit_s": protocol.wall_time_s,
                "population_size": protocol.population_size,
                "trace_limit": protocol.trace_limit,
                "thread_count": protocol.thread_count,
            },
        }
    )
    telemetry = row.get("telemetry")
    if not isinstance(telemetry, dict) or not telemetry:
        telemetry = _failure_telemetry(run, protocol)
        row["telemetry"] = telemetry
    if isinstance(telemetry, dict):
        instance = telemetry.setdefault("instance", {})
        instance["id"] = run.benchmark_id
        instance["family"] = run.family
        instance["checksum"] = _case_evidence_checksum(run.benchmark_id)
    return row


def _failure_row(
    run: PlannedProtocolRun,
    protocol: ComparisonProtocol,
    failure_type: str,
    message: str,
    stderr: str,
) -> dict[str, Any]:
    return {
        "benchmark_id": run.benchmark_id,
        "family": run.family,
        "model_style": run.model_style,
        "strategy": protocol.strategy,
        "solve_route": protocol.solve_route,
        "platform": _platform_coordinate(),
        "seed": run.seed,
        "thread_count": protocol.thread_count,
        "status": "error",
        "feasible": False,
        "verification_status": "not_run",
        "verification_passed": False,
        "verification_violations": [],
        "objective": None,
        "reference_objective": None,
        "gap_rel": None,
        "elapsed_seconds": protocol.wall_time_s,
        "effective_budget": {
            "max_iterations": protocol.max_iterations,
            "time_limit_s": protocol.wall_time_s,
            "population_size": protocol.population_size,
            "trace_limit": protocol.trace_limit,
            "thread_count": protocol.thread_count,
        },
        "strategy_config": {"strategy": protocol.strategy, "population_size": protocol.population_size},
        "diagnostics": {"fallback_attempts": 0, "fallback_successes": 0},
        "error": {"type": failure_type, "message": message, "stderr": stderr[-2000:]},
        "telemetry": _failure_telemetry(run, protocol),
    }


def _failure_telemetry(run: PlannedProtocolRun, protocol: ComparisonProtocol) -> dict[str, Any]:
    return {
        "schema": {"schema_version": 1},
        "identity": {"strategy": protocol.strategy, "seed": run.seed, "thread_count": protocol.thread_count},
        "instance": {
            "id": run.benchmark_id,
            "family": run.family,
            "checksum": _case_evidence_checksum(run.benchmark_id),
        },
        "budget": {},
        "outcome": {"status": "failed", "feasible": False, "objective_sense": "minimize"},
        "effort": {},
        "progress": [],
        "trace_overflow": {"trace_truncated": False, "omitted_incumbent_events": 0},
    }


def _install_wheel_environment(bootstrap_python: str, wheel: Path, environment_dir: Path) -> str:
    subprocess.run([bootstrap_python, "-m", "venv", str(environment_dir)], check=True, cwd=REPO_ROOT)
    python_executable = environment_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    subprocess.run(
        [str(python_executable), "-m", "pip", "install", str(wheel)],
        check=True,
        cwd=REPO_ROOT,
    )
    return str(python_executable)


def _runtime_identity(python_executable: str) -> dict[str, Any]:
    script = (
        "import importlib, importlib.metadata, json, platform, optagent; "
        "native = importlib.import_module('_optagent_native'); "
        "print(json.dumps({'version': importlib.metadata.version('optagent'), "
        "'package_file': optagent.__file__, 'native_file': native.__file__, "
        "'python': platform.python_version()}, sort_keys=True))"
    )
    completed = subprocess.run(
        [python_executable, "-c", script],
        cwd=REPO_ROOT,
        env={**os.environ, "OPTAGENT_BENCHMARK_USE_INSTALLED": "1"},
        text=True,
        capture_output=True,
        check=True,
    )
    return dict(json.loads(completed.stdout))


def _case_evidence_checksum(benchmark_id: str) -> str:
    from benchmarks.run import case_object_by_id

    case = case_object_by_id(benchmark_id)
    digest = hashlib.sha256()
    digest.update(json.dumps(dict(case.reference), sort_keys=True, separators=(",", ":")).encode("utf-8"))
    for key in ("data_path", "raw_path", "solution_raw_path"):
        value = case.data.get(key)
        if not value:
            continue
        path = Path(str(value))
        if path.exists():
            digest.update(key.encode("ascii"))
            digest.update(path.read_bytes())
    return "sha256:" + digest.hexdigest()


def _git_output(cwd: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def _platform_coordinate() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    if system == "darwin":
        system = "macos"
    if machine in {"amd64", "x64"}:
        machine = "x86_64"
    return f"{system}_{machine}"
