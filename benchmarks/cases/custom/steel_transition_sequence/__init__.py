from __future__ import annotations

from . import bundled
from . import expanded
from . import toy

CASES = (
    *toy.CASES,
    *bundled.CASES,
    *expanded.CASES,
)

INSTANCE_MODULES = (
    toy,
    bundled,
    expanded,
)
