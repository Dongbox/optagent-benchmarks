from __future__ import annotations

from . import a, b, e, f, golden, li, loggi, ortec, p, tai, x, xl, xml100

# This package aggregates concrete CVRPLIB CVRP instance modules.
CASES = (
    *a.CASES,
    *b.CASES,
    *e.CASES,
    *f.CASES,
    *golden.CASES,
    *li.CASES,
    *loggi.CASES,
    *ortec.CASES,
    *p.CASES,
    *tai.CASES,
    *x.CASES,
    *xl.CASES,
    *xml100.CASES,
)

INSTANCE_MODULES = (
    a, 
    b, 
    e, 
    f, 
    golden, 
    li, 
    loggi, 
    ortec, 
    p, 
    tai, 
    x, 
    xl, 
    xml100
)
