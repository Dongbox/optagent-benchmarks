from __future__ import annotations

from . import a
from . import berlin
from . import eil
from . import kroa
from . import pr

CASES = (
    *pr.CASES,
    *kroa.CASES,
    *a.CASES,
    *berlin.CASES,
    *eil.CASES,
)

INSTANCE_MODULES = (
    pr,
    kroa,
    a,
    berlin,
    eil,
)
