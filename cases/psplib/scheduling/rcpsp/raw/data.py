from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


# PSPLIB RCPSP 数据说明：
# - 当前 selected cases 使用 ScheduleOpt 暴露的 `.rcp` 文本。
# - 第 1 行是 activity_count 和 resource_count。
# - 第 2 行是每个可再生资源的容量。
# - 后续每行描述一个 activity：duration、各资源 demand、successor 数量和 successor 列表。
# - PSPLIB successor 在文件中是 1-based；loader 内部统一转为 0-based activity_id。
# - raw/ 保存已下载的公开原始文件；新增实例时优先把来源和格式写入 实例模块 与本文件注释。
DEFAULT_RAW_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class RcpspActivity:
    activity_id: int
    duration: int
    demands: tuple[int, ...]
    successors: tuple[int, ...]


@dataclass(frozen=True)
class RcpspInstance:
    name: str
    activity_count: int
    resource_count: int
    capacities: tuple[int, ...]
    activities: tuple[RcpspActivity, ...]

    @property
    def non_dummy_activity_count(self) -> int:
        return max(0, self.activity_count - 2)

    @property
    def horizon(self) -> int:
        return sum(activity.duration for activity in self.activities)

    @property
    def source_activity_id(self) -> int:
        return 0

    @property
    def sink_activity_id(self) -> int:
        return self.activity_count - 1


def parse_psplib_rcp_text(text: str, *, name: str) -> RcpspInstance:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 2:
        raise ValueError("PSPLIB .rcp data requires a header and capacity row")

    header = [int(item) for item in lines[0].split()]
    if len(header) != 2:
        raise ValueError("PSPLIB .rcp first row must contain activity count and resource count")
    activity_count, resource_count = header
    if activity_count <= 0 or resource_count <= 0:
        raise ValueError("PSPLIB .rcp activity and resource counts must be positive")

    capacities = tuple(int(item) for item in lines[1].split())
    if len(capacities) != resource_count:
        raise ValueError(f"expected {resource_count} resource capacities, found {len(capacities)}")

    activity_lines = lines[2:]
    if len(activity_lines) != activity_count:
        raise ValueError(f"expected {activity_count} activity rows, found {len(activity_lines)}")

    activities: list[RcpspActivity] = []
    for activity_id, line in enumerate(activity_lines):
        values = [int(item) for item in line.split()]
        minimum = 1 + resource_count + 1
        if len(values) < minimum:
            raise ValueError(f"activity row {activity_id + 1} is too short")
        duration = values[0]
        demands = tuple(values[1 : 1 + resource_count])
        successor_count = values[1 + resource_count]
        successor_values = values[2 + resource_count :]
        if len(successor_values) != successor_count:
            raise ValueError(
                f"activity row {activity_id + 1} declares {successor_count} successors "
                f"but provides {len(successor_values)}"
            )
        successors = tuple(successor - 1 for successor in successor_values)
        if duration < 0:
            raise ValueError(f"activity {activity_id + 1} duration must be non-negative")
        if any(demand < 0 for demand in demands):
            raise ValueError(f"activity {activity_id + 1} demands must be non-negative")
        for successor in successors:
            if successor < 0 or successor >= activity_count:
                raise ValueError(f"activity {activity_id + 1} successor out of range: {successor + 1}")
        activities.append(
            RcpspActivity(
                activity_id=activity_id,
                duration=duration,
                demands=demands,
                successors=successors,
            )
        )

    return RcpspInstance(
        name=name,
        activity_count=activity_count,
        resource_count=resource_count,
        capacities=capacities,
        activities=tuple(activities),
    )


def load_rcpsp_case(
    case: dict[str, Any],
    *,
    cache_dir: str | Path = DEFAULT_RAW_DIR,
    allow_download: bool = True,
) -> RcpspInstance:
    data = case.get("data", {})
    instance_name = str(case.get("instance") or case["benchmark_id"].removeprefix("psplib_"))
    local_path = data.get("local_path")
    if local_path:
        return parse_psplib_rcp_text(Path(local_path).read_text(encoding="utf-8"), name=instance_name)

    path = Path(cache_dir) / f"{instance_name}.rcp"
    if path.exists():
        return parse_psplib_rcp_text(path.read_text(encoding="utf-8"), name=instance_name)

    urls = [str(url) for url in [data.get("instance_url"), *data.get("mirror_urls", [])] if url]
    if not urls:
        raise ValueError(f"case {case['benchmark_id']} does not provide an instance_url")
    if not allow_download:
        raise FileNotFoundError(f"cached PSPLIB file not found and downloads are disabled: {path}")

    path.parent.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    for url in urls:
        try:
            text = _download_text(url)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            errors.append(f"{url}: {type(exc).__name__}: {exc}")
            continue
        path.write_text(text, encoding="utf-8")
        return parse_psplib_rcp_text(text, name=instance_name)
    raise RuntimeError(
        f"failed to download PSPLIB case {case['benchmark_id']} from {len(urls)} source(s): "
        + " | ".join(errors)
    )


def _download_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": "optagent-benchmark/1.0"})
    with urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", errors="replace")
