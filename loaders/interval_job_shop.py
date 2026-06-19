from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_CACHE = REPO_ROOT / "benchmarks" / "data-cache" / "interval_job_shop"


@dataclass(frozen=True)
class JobShopOperation:
    job: int
    operation: int
    machine: int
    duration: int


@dataclass(frozen=True)
class JobShopInstance:
    name: str
    jobs: int
    machines: int
    operations: tuple[JobShopOperation, ...]
    family: str | None = None
    family_long: str | None = None
    year: str | None = None

    @property
    def operation_count(self) -> int:
        return len(self.operations)

    @property
    def horizon(self) -> int:
        return sum(operation.duration for operation in self.operations)

    def operations_by_job(self) -> dict[int, tuple[JobShopOperation, ...]]:
        grouped: dict[int, list[JobShopOperation]] = {job: [] for job in range(self.jobs)}
        for operation in self.operations:
            grouped.setdefault(operation.job, []).append(operation)
        return {
            job: tuple(sorted(items, key=lambda item: item.operation))
            for job, items in sorted(grouped.items())
        }

    def operations_by_machine(self) -> dict[int, tuple[JobShopOperation, ...]]:
        grouped: dict[int, list[JobShopOperation]] = {machine: [] for machine in range(self.machines)}
        for operation in self.operations:
            grouped.setdefault(operation.machine, []).append(operation)
        return {
            machine: tuple(sorted(items, key=lambda item: (item.job, item.operation)))
            for machine, items in sorted(grouped.items())
        }


def parse_scheduleopt_jsplib_json(text: str) -> JobShopInstance:
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("ScheduleOpt JSPLIB JSON root must be an object")

    name = str(payload.get("instance") or "").strip()
    if not name:
        raise ValueError("ScheduleOpt JSPLIB JSON requires an instance name")

    jobs = int(payload.get("jobs") or 0)
    machines = int(payload.get("machines") or 0)
    rows = payload.get("data")
    if jobs <= 0 or machines <= 0:
        raise ValueError("ScheduleOpt JSPLIB JSON requires positive jobs and machines")
    if not isinstance(rows, list):
        raise ValueError("ScheduleOpt JSPLIB JSON data must be a list")

    operations: list[JobShopOperation] = []
    seen: set[tuple[int, int]] = set()
    for raw in rows:
        if not isinstance(raw, dict):
            raise ValueError("ScheduleOpt JSPLIB JSON operation rows must be objects")
        operation = JobShopOperation(
            job=int(raw["job"]),
            operation=int(raw["operation"]),
            machine=int(raw["machine"]),
            duration=int(raw["duration"]),
        )
        if operation.job < 0 or operation.job >= jobs:
            raise ValueError(f"operation job index out of range: {operation.job}")
        if operation.operation < 0 or operation.operation >= machines:
            raise ValueError(f"operation index out of range: {operation.operation}")
        if operation.machine < 0 or operation.machine >= machines:
            raise ValueError(f"operation machine index out of range: {operation.machine}")
        if operation.duration < 0:
            raise ValueError(f"operation duration must be non-negative: {operation.duration}")
        key = (operation.job, operation.operation)
        if key in seen:
            raise ValueError(f"duplicate operation for job/order pair: {key}")
        seen.add(key)
        operations.append(operation)

    expected_count = jobs * machines
    if len(operations) != expected_count:
        raise ValueError(f"expected {expected_count} operations, found {len(operations)}")
    expected_pairs = {(job, operation) for job in range(jobs) for operation in range(machines)}
    missing_pairs = expected_pairs - seen
    if missing_pairs:
        missing = sorted(missing_pairs)[:5]
        raise ValueError(f"missing job/order operation pairs: {missing}")

    return JobShopInstance(
        name=name,
        jobs=jobs,
        machines=machines,
        operations=tuple(sorted(operations, key=lambda item: (item.job, item.operation))),
        family=str(payload["family"]) if payload.get("family") is not None else None,
        family_long=str(payload["family_long"]) if payload.get("family_long") is not None else None,
        year=str(payload["year"]) if payload.get("year") is not None else None,
    )


def load_job_shop_case(
    case: dict[str, Any],
    *,
    cache_dir: str | Path = DEFAULT_DATA_CACHE,
    allow_download: bool = True,
) -> JobShopInstance:
    data = case.get("data", {})
    local_path = data.get("local_path")
    if local_path:
        return parse_scheduleopt_jsplib_json(Path(local_path).read_text(encoding="utf-8"))

    instance_name = str(case.get("instance") or case["benchmark_id"].removeprefix("jsplib_"))
    path = Path(cache_dir) / f"{instance_name}.json"
    if path.exists():
        return parse_scheduleopt_jsplib_json(path.read_text(encoding="utf-8"))

    urls = [str(url) for url in [data.get("instance_url"), *data.get("mirror_urls", [])] if url]
    if not urls:
        raise ValueError(f"case {case['benchmark_id']} does not provide an instance_url")
    if not allow_download:
        raise FileNotFoundError(f"cached JSPLIB file not found and downloads are disabled: {path}")

    path.parent.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    for url in urls:
        try:
            text = _download_text(url)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            errors.append(f"{url}: {type(exc).__name__}: {exc}")
            continue
        path.write_text(text, encoding="utf-8")
        return parse_scheduleopt_jsplib_json(text)
    raise RuntimeError(
        f"failed to download JSPLIB case {case['benchmark_id']} from {len(urls)} source(s): "
        + " | ".join(errors)
    )


def _download_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": "optagent-benchmark/1.0"})
    with urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", errors="replace")
