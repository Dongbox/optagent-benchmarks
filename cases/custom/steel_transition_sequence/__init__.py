from __future__ import annotations

from . import bundled
from . import toy

CASES = (
    *toy.CASES,
    *bundled.CASES,
)

INSTANCE_MODULES = (
    toy,
    bundled,
)
