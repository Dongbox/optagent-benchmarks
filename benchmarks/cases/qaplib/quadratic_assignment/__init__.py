from __future__ import annotations

from . import bur
from . import chr
from . import els
from . import esc
from . import had
from . import kra
from . import lipa
from . import nug
from . import scr
from . import sko
from . import ste
from . import tai
from . import tho
from . import wil

CASES = (
    *bur.CASES,
    *chr.CASES,
    *els.CASES,
    *esc.CASES,
    *had.CASES,
    *kra.CASES,
    *lipa.CASES,
    *nug.CASES,
    *scr.CASES,
    *sko.CASES,
    *ste.CASES,
    *tai.CASES,
    *tho.CASES,
    *wil.CASES,
)

INSTANCE_MODULES = (
    bur,
    chr,
    els,
    esc,
    had,
    kra,
    lipa,
    nug,
    scr,
    sko,
    ste,
    tai,
    tho,
    wil,
)
