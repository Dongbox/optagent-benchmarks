"""Benchmark runner entrypoints and shared result schemas."""
from __future__ import annotations

__all__ = ["IMPLEMENTED_FAMILIES", "run_benchmark_suite"]


def __getattr__(name: str):
    if name in __all__:
        from benchmarks.runners import suite

        return getattr(suite, name)
    raise AttributeError(name)
