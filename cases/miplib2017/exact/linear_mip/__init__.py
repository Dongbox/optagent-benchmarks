from __future__ import annotations

from . import academictimetable
from . import air
from . import case_50v
from . import fast
from . import ran14x18_disj
from . import reblock

CASES = (
    *reblock.CASES,
    *air.CASES,
    *fast.CASES,
    *academictimetable.CASES,
    *case_50v.CASES,
    *ran14x18_disj.CASES,
)

INSTANCE_MODULES = (
    reblock,
    air,
    fast,
    academictimetable,
    case_50v,
    ran14x18_disj,
)
