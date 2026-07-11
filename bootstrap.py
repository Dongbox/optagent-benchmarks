from __future__ import annotations

import os
import sys
import sysconfig
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"


def prefer_local_development_paths() -> None:
    """Prefer repo-local Python and native build outputs for benchmark runs."""

    if os.environ.get("OPTAGENT_BENCHMARK_USE_INSTALLED") == "1":
        return

    sys.meta_path = [finder for finder in sys.meta_path if type(finder).__module__ != "_optagent_editable"]
    preferred_paths = (SRC_ROOT, *_candidate_native_build_dirs())
    for path in reversed(preferred_paths):
        if not path.exists():
            continue
        path_text = str(path)
        sys.path = [path_text, *[item for item in sys.path if item != path_text]]


def _candidate_native_build_dirs() -> tuple[Path, ...]:
    ext_suffix = str(sysconfig.get_config_var("EXT_SUFFIX") or "")
    candidates = [
        REPO_ROOT / "build" / "native-debug",
        REPO_ROOT / "build" / "native-debug-py314",
    ]
    matching = [path for path in candidates if any(path.glob(f"_optagent_native*{ext_suffix}"))]
    return tuple(matching + [path for path in candidates if path not in matching])
