from __future__ import annotations

from . import abz
from . import dmu
from . import ft
from . import la
from . import swv

# 本包汇总实例声明模块；同一公开系列可在一个模块中暴露多个实例。
CASES = (
    *abz.CASES,
    *ft.CASES,
    *la.CASES,
    *dmu.CASES,
    *swv.CASES,
)

INSTANCE_MODULES = (
    abz,
    ft,
    la,
    dmu,
    swv,
)
