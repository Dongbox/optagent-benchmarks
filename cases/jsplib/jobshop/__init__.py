from __future__ import annotations

from . import abz
from . import dmu
from . import ft
from . import la
from . import orb
from . import swv
from . import tai
from . import yn

# This package aggregates concrete job-shop benchmark instance modules.
CASES = (
    *abz.CASES,
    *ft.CASES,
    *la.CASES,
    *orb.CASES,
    *dmu.CASES,
    *swv.CASES,
    *tai.CASES,
    *yn.CASES,
)

INSTANCE_MODULES = (
    abz,
    ft,
    la,
    orb,
    dmu,
    swv,
    tai,
    yn,
)
