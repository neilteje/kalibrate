"""KALIBRATE top-level agent.

Wires the five core modules into a single forecasting episode. Each call to
`run_episode` is independent (no cross-episode memory). Returns a structured
result dict that is consumed by the evaluation harness.
"""
from __future__ import annotations

import time
from typing import Any

from . import evidence_extractor, forecaster, market_state, risk_controller, tool_router


def run_episode(
    task: dict[str, Any],
    *,
    tool_budget: int = tool_router.DEFAULT_TOOL_BUDGET,
    forecaster_model: str | None = None,
    forecaster_temperature: float = 0.2,
    abstain_enabled: bool = True,
) -> dict[str, Any]:
    """Run a single forecasting episode.

    Parameters
    ----------
    task : dict
        Raw task dictionary as loaded from `tasks/T*.json`.
    tool_budget : int
        Maximum number of Tavily search calls. Set to 0 for market-only.
    forecaster_model : str | None
        Override the default forecasting model.
    forecaster_temperature : float
        Temperature for the forecasting call.
    abstain_enabled : bool
        If False, the risk controller will never set abstain=True (always
        returns p_hat as p_final).

    Returns
    -------
    dict with the result trace, suitable for JSON serialization.
    """
    t0 = time.perf_counter()
    state = market_state.build_state(task)

    if tool_budget > 0:
        retrieval = tool_router.route_and_retrieve(state, budget=tool_budget)
    else:
        retrieval = {
            "decision": {"invoke_tools": False, "queries": [], "rationale": "tool_budget=0"},
            "tool_calls": 0,
            "documents": [],
        }

    if retrieval["documents"]:
        evidence = evidence_extractor.extract(state, retrieval["documents"])
    else:
        evidence = None

    fc_kwargs: dict[str, Any] = {"temperature": forecaster_temperature}
    if forecaster_model is not None:
        fc_kwargs["model"] = forecaster_model
    fc = forecaster.forecast(state, evidence=evidence, **fc_kwargs)

    if abstain_enabled:
        risk = risk_controller.decide(fc, state, evidence)
    else:
        risk = {
            "abstain": False,
            "p_final": float(fc["p_hat"]),
            "reasons": ["abstain_disabled"],
        }

    runtime = time.perf_counter() - t0

    return {
        "task_id": task["task_id"],
        "system": "kalibrate_full" if tool_budget > 0 else "kalibrate_market_only",
        "p_final": risk["p_final"],
        "p_hat_raw": fc["p_hat"],
        "abstain": risk["abstain"],
        "abstain_reasons": risk["reasons"],
        "confidence": fc["confidence"],
        "tool_calls": retrieval["tool_calls"],
        "documents_retrieved": len(retrieval["documents"]),
        "evidence_summary": (evidence or {}).get("aggregate"),
        "router_decision": retrieval["decision"],
        "forecast_reasoning": fc["reasoning_summary"],
        "signals_used": fc["signals_used"],
        "runtime_s": round(runtime, 3),
    }
