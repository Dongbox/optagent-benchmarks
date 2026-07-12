from __future__ import annotations

from . import barnes
from . import behnke
from . import brandimarte
from . import dauzere
from . import fattahi
from . import hurink
from . import kacem

# This package aggregates concrete flexible job-shop benchmark instance modules.
CASES = (
    *fattahi.CASES,
    *kacem.CASES,
    *brandimarte.CASES,
    *hurink.CASES,
    *barnes.CASES,
    *behnke.CASES,
    *dauzere.CASES,
)

INSTANCE_MODULES = (
    fattahi,
    kacem,
    brandimarte,
    hurink,
    barnes,
    behnke,
    dauzere,
)
