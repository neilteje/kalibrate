"""B4: KALIBRATE Ablation (Market-Only).

The full KALIBRATE pipeline with tool invocation disabled (B=0). Skips
tool router, evidence extractor; the forecaster sees only the market
state. Risk controller can still abstain based on confidence/volatility,
but never on evidence relevance (since there is none).

Isolates the value of external evidence gathering.
"""
from __future__ import annotations

from typing import Any

from agent.agent import run_episode


SYSTEM_NAME = "market_only"


def run(task: dict[str, Any]) -> dict[str, Any]:
    result = run_episode(task, tool_budget=0)
    result["system"] = SYSTEM_NAME
    return result
