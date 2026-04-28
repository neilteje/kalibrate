"""B2: Single-Prompt LLM baseline.

A strong language model receives the full market state JSON in a single
prompt and outputs a probability with no tool use, iterative reasoning,
or structured extraction. Tests whether agentic workflow adds value
beyond raw model capability.
"""
from __future__ import annotations

import json
import time
from typing import Any

from agent import market_state
from agent.forecaster import _FORECAST_SCHEMA, P_CEIL, P_FLOOR
from agent.llm_clients import DEFAULT_OPENAI_FRONTIER, openai_client


SYSTEM_NAME = "single_prompt"


_SYSTEM_PROMPT = f"""You are a probabilistic forecaster. Given a market state, \
output a calibrated YES probability.

Output ONLY valid JSON with these fields:
- p_hat: float in [{P_FLOOR}, {P_CEIL}]
- confidence: float in [0, 1]
- signals_used: list of short strings
- reasoning_summary: at most 2 sentences

You have NO tools. Reason from the market state alone."""


def run(
    task: dict[str, Any], model: str = DEFAULT_OPENAI_FRONTIER, temperature: float = 0.3
) -> dict[str, Any]:
    t0 = time.perf_counter()
    state = market_state.build_state(task)
    client = openai_client()
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps({"market_state": state})},
        ],
        response_format=_FORECAST_SCHEMA,
        temperature=temperature,
    )
    parsed = json.loads(resp.choices[0].message.content or "{}")
    p_hat = max(P_FLOOR, min(P_CEIL, float(parsed.get("p_hat", 0.5))))
    return {
        "task_id": task["task_id"],
        "system": SYSTEM_NAME,
        "p_final": p_hat,
        "p_hat_raw": p_hat,
        "abstain": False,
        "abstain_reasons": [],
        "confidence": float(parsed.get("confidence", 0.5)),
        "tool_calls": 0,
        "documents_retrieved": 0,
        "forecast_reasoning": parsed.get("reasoning_summary", ""),
        "signals_used": parsed.get("signals_used", []),
        "runtime_s": round(time.perf_counter() - t0, 3),
    }
