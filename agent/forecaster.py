"""Forecasting Module.

Combines normalized market state with structured evidence features to
produce a calibrated probability forecast. The output schema is enforced
through OpenAI structured output. Probabilities are clipped to [0.05, 0.95]
to prevent the catastrophic Brier scores that result from unbounded
overconfidence.
"""
from __future__ import annotations

import json
from typing import Any

from .llm_clients import DEFAULT_OPENAI_MODEL, openai_client


P_FLOOR = 0.05
P_CEIL = 0.95


_FORECASTER_SYSTEM_PROMPT = f"""You are a calibrated probabilistic forecaster.

You receive a JSON market state and (optionally) a structured evidence \
summary describing retrieved documents. You must produce a probability that \
the market resolves YES according to the resolution_criteria.

Rules:
- Output ONLY a valid JSON object with exactly the required fields.
- p_hat must be a float in [{P_FLOOR}, {P_CEIL}].
- confidence reflects YOUR self-assessed certainty in p_hat (not the probability itself).
- reasoning_summary must be at most 2 sentences.
- Treat price_history as informative but not infallible; integrate it with evidence and base rates.
- Be honest about uncertainty; do not gravitate to 0.5 unless truly ambivalent."""


_FORECAST_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "Forecast",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "p_hat": {"type": "number", "minimum": 0, "maximum": 1},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "signals_used": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "reasoning_summary": {"type": "string"},
            },
            "required": ["p_hat", "confidence", "signals_used", "reasoning_summary"],
        },
    },
}


def _clip(p: float) -> float:
    return max(P_FLOOR, min(P_CEIL, float(p)))


def forecast(
    state: dict[str, Any],
    evidence: dict[str, Any] | None = None,
    model: str = DEFAULT_OPENAI_MODEL,
    temperature: float = 0.2,
) -> dict[str, Any]:
    """Produce a probability forecast for the market state.

    `evidence` is the dict returned by `evidence_extractor.extract()`. Pass
    None for a market-only forecast.
    """
    payload: dict[str, Any] = {"market_state": state}
    if evidence is not None and evidence.get("per_document"):
        payload["evidence_summary"] = evidence["aggregate"]
        payload["evidence_documents"] = [
            {
                "title": d.get("title", ""),
                "sentiment": d["sentiment"],
                "source_credibility": d["source_credibility"],
                "event_type": d["event_type"],
                "relevance_score": d["relevance_score"],
                "recency_weight": d["recency_weight"],
                "justification": d["justification"],
            }
            for d in evidence["per_document"]
        ]
    else:
        payload["evidence_summary"] = None

    client = openai_client()
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _FORECASTER_SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(payload)},
        ],
        response_format=_FORECAST_SCHEMA,
        temperature=temperature,
    )
    out = json.loads(resp.choices[0].message.content or "{}")
    out["p_hat"] = _clip(out.get("p_hat", 0.5))
    out["confidence"] = max(0.0, min(1.0, float(out.get("confidence", 0.5))))
    return out
