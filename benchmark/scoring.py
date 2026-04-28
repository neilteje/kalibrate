"""Scoring rules for the POPCAST benchmark.

All metrics treat outcomes as binary y in {0, 1} and forecasts as p in
[0, 1]. Lower Brier and log-loss are better; higher TSR is better.
"""
from __future__ import annotations

import math


_LOG_FLOOR = 1e-9


def brier(p: float, y: int) -> float:
    return (float(p) - float(y)) ** 2


def log_loss(p: float, y: int) -> float:
    p = max(_LOG_FLOOR, min(1.0 - _LOG_FLOOR, float(p)))
    y = int(y)
    return -(y * math.log(p) + (1 - y) * math.log(1 - p))


def task_success(p: float, y: int) -> int:
    """1 if the binary direction (p > 0.5) matches y, else 0. Ties (p==0.5)
    are scored as misses."""
    return int((float(p) > 0.5) == bool(int(y)))
