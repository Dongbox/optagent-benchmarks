from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

import benchmarks.telemetry_artifacts as telemetry_artifacts
from benchmarks.presentation.common import REPO_ROOT, utc_timestamp, write_json


DEFAULT_DASHBOARD_ROOT = REPO_ROOT / "docs" / "evals" / "benchmark-suite" / "dashboards"


def generate_dashboard(
    artifact_dir: str | Path,
    *,
    output_root: str | Path = DEFAULT_DASHBOARD_ROOT,
    dashboard_id: str | None = None,
) -> dict[str, Any]:
    """Generate static dashboard files from published telemetry artifacts."""

    artifact_path = Path(artifact_dir)
    published = telemetry_artifacts.load_published_artifacts(artifact_path)
    output_dir = Path(output_root) / (dashboard_id or f"dashboard-{utc_timestamp()}")
    output_dir.mkdir(parents=True, exist_ok=False)

    dashboard = {
        **published["dashboard"],
        "dashboard_id": output_dir.name,
        "artifact_dir": str(artifact_path),
        "manifest": published["manifest"],
    }
    write_json(output_dir / "manifest.json", published["manifest"])
    write_json(output_dir / "dashboard.json", dashboard)
    (output_dir / "dashboard.md").write_text(
        telemetry_artifacts.render_dashboard_markdown(dashboard),
        encoding="utf-8",
    )
    return {**dashboard, "output_dir": str(output_dir)}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a static dashboard from telemetry artifacts.")
    parser.add_argument("artifact_dir")
    parser.add_argument("--output-root", default=str(DEFAULT_DASHBOARD_ROOT))
    parser.add_argument("--dashboard-id")
    args = parser.parse_args(argv)

    dashboard = generate_dashboard(
        args.artifact_dir,
        output_root=args.output_root,
        dashboard_id=args.dashboard_id,
    )
    print(json.dumps(dashboard, indent=2, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
