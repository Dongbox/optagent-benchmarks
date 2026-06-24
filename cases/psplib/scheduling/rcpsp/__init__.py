from __future__ import annotations

from . import j90_1
from . import j90_2
from . import j90_5
from . import j90_6

CASES = (
    *j90_1.CASES,
    *j90_2.CASES,
    *j90_5.CASES,
    *j90_6.CASES,
)

INSTANCE_MODULES = (
    j90_1,
    j90_2,
    j90_5,
    j90_6,
)
