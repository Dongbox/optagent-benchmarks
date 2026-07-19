from __future__ import annotations

from . import j30, j60, j90, j120

CASES = (
    *j30.CASES,
    *j60.CASES,
    *j90.CASES,
    *j120.CASES,
)

INSTANCE_MODULES = (j30, j60, j90, j120)
