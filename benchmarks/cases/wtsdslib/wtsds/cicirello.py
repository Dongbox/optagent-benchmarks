from __future__ import annotations

from ._domain import make_wtsds_cases

CASES = make_wtsds_cases(case_module=__name__)
