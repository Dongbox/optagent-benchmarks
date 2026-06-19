from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
LOCAL_NATIVE_BUILD = REPO_ROOT / "build" / "native-debug"
SRC_ROOT = REPO_ROOT / "src"


def prefer_local_development_paths() -> None:
    """Prefer repo-local Python and native build outputs for benchmark runs."""

    for path in (SRC_ROOT, LOCAL_NATIVE_BUILD):
        if not path.exists():
            continue
        path_text = str(path)
        sys.path = [path_text, *[item for item in sys.path if item != path_text]]
