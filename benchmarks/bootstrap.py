from __future__ import annotations

import os
import sys
import sysconfig
from pathlib import Path


def prefer_local_development_paths() -> None:
    """Prefer an explicitly configured OptAgent source checkout."""

    source_root = os.environ.get("OPTAGENT_SOURCE_ROOT")
    if not source_root:
        return

    repo_root = Path(source_root).expanduser().resolve()
    sys.meta_path = [finder for finder in sys.meta_path if type(finder).__module__ != "_optagent_editable"]
    preferred_paths = (repo_root / "src", *_candidate_native_build_dirs(repo_root))
    for path in reversed(preferred_paths):
        if not path.exists():
            continue
        path_text = str(path)
        sys.path = [path_text, *[item for item in sys.path if item != path_text]]


def _candidate_native_build_dirs(repo_root: Path) -> tuple[Path, ...]:
    ext_suffix = str(sysconfig.get_config_var("EXT_SUFFIX") or "")
    candidates = [
        repo_root / "build" / "native-debug-ninja",
        repo_root / "build" / "native-debug",
        repo_root / "build" / "native-debug-py314",
    ]
    matching = [path for path in candidates if any(path.glob(f"_optagent_native*{ext_suffix}"))]
    return tuple(matching + [path for path in candidates if path not in matching])
