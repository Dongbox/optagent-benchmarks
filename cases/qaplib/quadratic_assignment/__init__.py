from __future__ import annotations

from . import chr
from . import had
from . import lipa
from . import nug

CASES = (
    *nug.CASES,
    *had.CASES,
    *lipa.CASES,
    *chr.CASES,
)

INSTANCE_MODULES = (
    nug,
    had,
    lipa,
    chr,
)
