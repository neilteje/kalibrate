"""Evidence Extractor.

Converts raw retrieved documents into structured evidence features. Each
document is annotated with sentiment, source credibility, recency weight,
event type, and relevance score. The aggregated summary is consumed by the
forecasting module to produce a calibrated probability.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from typing import Any

from .llm_clients import DEFAULT_OPENAI_MODEL, openai_client


_EXTRACTOR_SYSTEM_PROMPT = """You convert raw retrieved documents into \
structured evidence features for a probabilistic forecasting agent.

For each document, output:
- sentiment: one of "positive", "negative", "neutral" relative to the YES outcome of the market question
- source_credibility: one of "verified_outlet", "social_media", "rumor_or_leak", "unknown"
- event_type: one of "announcement", "award_signal", "rumor", "financial_report", "trending_moment", "analysis", "other"
- relevance_score: float in [0, 1] for how directly the document bears on the market question
- one-line justification

Output ONLY a valid JSON object."""


_EXTRACTION_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "EvidenceExtraction",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "documents": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "url": {"type": "string"},
                            "sentiment": {
                                "type": "string",
                                "enum": ["positive", "negative", "neutral"],
                            },
                            "source_credibility": {
                                "type": "string",
                                "enum": [
                                    "verified_outlet",
                                    "social_media",
                                    "rumor_or_leak",
                                    "unknown",
                                ],
                            },
                            "event_type": {
                                "type": "string",
                                "enum": [
                                    "announcement",
                                    "award_signal",
                                    "rumor",
                                    "financial_report",
                                    "trending_moment",
                                    "analysis",
                                    "other",
                                ],
                            },
                            "relevance_score": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                            },
                            "justification": {"type": "string"},
                        },
                        "required": [
                            "url",
                            "sentiment",
                            "source_credibility",
                            "event_type",
                            "relevance_score",
                            "justification",
                        ],
                    },
                }
            },
            "required": ["documents"],
        },
    },
}


def _parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)


def _recency_weight(pub_date: str | None, decision_timestamp: str, half_life_days: float = 14.0) -> float:
    """Exponential decay based on days between publication and decision time."""
    if not pub_date:
        return 0.5
    try:
        pub = _parse_iso(pub_date)
        cutoff = _parse_iso(decision_timestamp)
        days = max(0.0, (cutoff - pub).total_seconds() / 86400.0)
        return float(math.exp(-days / half_life_days))
    except Exception:
        return 0.5


def extract(
    state: dict[str, Any], documents: list[dict[str, Any]]
) -> dict[str, Any]:
    """Convert raw documents into structured features. Returns a dict with
    per-document features and an aggregated summary."""
    if not documents:
        return {
            "per_document": [],
            "aggregate": {
                "n_documents": 0,
                "n_high_relevance": 0,
                "directional_score": 0.0,
                "credibility_mix": {},
                "max_relevance": 0.0,
            },
        }

    user_payload = {
        "market_question": state["title"],
        "resolution_criteria": state["resolution_criteria"],
        "decision_timestamp": state["decision_timestamp"],
        "documents": [
            {
                "url": d["url"],
                "title": d.get("title", ""),
                "content": d.get("content", "")[:1200],
                "published_date": d.get("published_date"),
            }
            for d in documents
        ],
    }
    client = openai_client()
    resp = client.chat.completions.create(
        model=DEFAULT_OPENAI_MODEL,
        messages=[
            {"role": "system", "content": _EXTRACTOR_SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(user_payload)},
        ],
        response_format=_EXTRACTION_SCHEMA,
        temperature=0.0,
    )
    parsed = json.loads(resp.choices[0].message.content or "{}").get("documents", [])

    by_url = {d["url"]: d for d in documents}
    per_doc: list[dict[str, Any]] = []
    for feat in parsed:
        url = feat.get("url", "")
        raw = by_url.get(url, {})
        feat["recency_weight"] = _recency_weight(
            raw.get("published_date"), state["decision_timestamp"]
        )
        feat["title"] = raw.get("title", "")
        feat["published_date"] = raw.get("published_date")
        per_doc.append(feat)

    # Aggregate signal: sentiment-weighted by relevance and recency.
    sentiment_value = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}
    credibility_weight = {
        "verified_outlet": 1.0,
        "social_media": 0.55,
        "rumor_or_leak": 0.45,
        "unknown": 0.5,
    }
    weighted_sum = 0.0
    weight_total = 0.0
    cred_mix: dict[str, int] = {}
    for d in per_doc:
        rel = float(d["relevance_score"])
        rec = float(d["recency_weight"])
        cred = credibility_weight.get(d["source_credibility"], 0.5)
        sv = sentiment_value.get(d["sentiment"], 0.0)
        w = rel * rec * cred
        weighted_sum += sv * w
        weight_total += w
        cred_mix[d["source_credibility"]] = cred_mix.get(d["source_credibility"], 0) + 1

    directional_score = (weighted_sum / weight_total) if weight_total > 0 else 0.0
    n_high_rel = sum(1 for d in per_doc if d["relevance_score"] >= 0.6)
    max_rel = max((d["relevance_score"] for d in per_doc), default=0.0)

    return {
        "per_document": per_doc,
        "aggregate": {
            "n_documents": len(per_doc),
            "n_high_relevance": n_high_rel,
            "directional_score": float(directional_score),
            "credibility_mix": cred_mix,
            "max_relevance": float(max_rel),
        },
    }
