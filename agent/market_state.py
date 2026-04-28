"""Market State Constructor.

Loads a POPCAST task JSON file and produces the normalized market state passed
to all downstream KALIBRATE modules. The state intentionally excludes any
post-decision information (the `outcome` and `notes_for_evaluation` fields are
stripped before being shown to the agent).
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


# Fields that must be hidden from the agent at forecast time.
_HIDDEN_FIELDS = ("outcome", "notes_for_evaluation")


def _hours_until(start_iso: str, end_iso: str) -> float:
    start = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
    end = datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
    return max(0.0, (end - start).total_seconds() / 3600.0)


def load_task(path: str | Path) -> dict[str, Any]:
    """Read a raw task JSON file (including ground-truth outcome)."""
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_state(task: dict[str, Any]) -> dict[str, Any]:
    """Construct the agent-visible market state from a raw task dict.

    The returned dict contains everything an agent should be allowed to see:
    market metadata, price history, volatility/liquidity proxies, and a
    derived `time_to_resolution_hours` field. Ground-truth fields are
    excluded.
    """
    state: dict[str, Any] = {
        "task_id": task["task_id"],
        "title": task["title"],
        "domain": task["domain"],
        "resolution_criteria": task["resolution_criteria"],
        "decision_timestamp": task["decision_timestamp"],
        "resolution_timestamp": task["resolution_timestamp"],
        "time_to_resolution_hours": _hours_until(
            task["decision_timestamp"], task["resolution_timestamp"]
        ),
        "price_history": list(task.get("price_history", [])),
        "volatility_proxy": float(task.get("volatility_proxy", 0.0)),
        "liquidity_proxy": float(task.get("liquidity_proxy", 0.0)),
        "context_hint": task.get("context_hint", ""),
    }
    for field in _HIDDEN_FIELDS:
        state.pop(field, None)
    return state


def get_outcome(task: dict[str, Any]) -> int:
    """Read ground-truth outcome (used by the eval harness, not the agent)."""
    return int(task["outcome"])
