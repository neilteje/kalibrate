"""B1: Random / Prior baseline. Always outputs p=0.5."""
from __future__ import annotations

import time
from typing import Any


SYSTEM_NAME = "random"


def run(task: dict[str, Any]) -> dict[str, Any]:
    t0 = time.perf_counter()
    return {
        "task_id": task["task_id"],
        "system": SYSTEM_NAME,
        "p_final": 0.5,
        "p_hat_raw": 0.5,
        "abstain": False,
        "abstain_reasons": [],
        "confidence": 0.0,
        "tool_calls": 0,
        "documents_retrieved": 0,
        "forecast_reasoning": "Constant prior of 0.5.",
        "signals_used": [],
        "runtime_s": round(time.perf_counter() - t0, 3),
    }
