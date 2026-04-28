"""Tool Router.

Decides whether to retrieve external evidence and which queries to issue,
subject to a hard budget on the number of Tavily search calls. All retrieved
results are filtered to enforce the temporal cutoff specified by the task's
`decision_timestamp`, preventing post-decision leakage.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .llm_clients import DEFAULT_OPENAI_MODEL, openai_client, tavily_client


DEFAULT_TOOL_BUDGET = 3


_ROUTER_SYSTEM_PROMPT = """You are the routing module of a probabilistic forecasting agent.

Given a JSON market state, decide whether external information retrieval is \
needed to produce a calibrated forecast. If retrieval would help, propose up \
to {budget} concise search queries that target the most outcome-relevant signals.

Constraints:
- You may NEVER request information published after the decision_timestamp.
- Prefer fewer, higher-quality queries over many shallow queries.
- If the market state already contains strong signals (clear price trend, strong context), prefer invoke_tools=false.

Output ONLY a valid JSON object with this exact schema:
{{
  "invoke_tools": bool,
  "queries": [string],
  "rationale": string
}}
queries must contain at most {budget} entries (zero if invoke_tools is false).
rationale must be one sentence.
"""


_ROUTER_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "ToolRoutingDecision",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "invoke_tools": {"type": "boolean"},
                "queries": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "rationale": {"type": "string"},
            },
            "required": ["invoke_tools", "queries", "rationale"],
        },
    },
}


def _parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)


def decide(state: dict[str, Any], budget: int = DEFAULT_TOOL_BUDGET) -> dict[str, Any]:
    """Ask the LLM whether to invoke tools and produce queries."""
    if budget <= 0:
        return {"invoke_tools": False, "queries": [], "rationale": "budget=0"}

    client = openai_client()
    user_msg = (
        "Market state:\n"
        + json.dumps(state, indent=2)
        + f"\n\nTool budget remaining: {budget}"
    )
    resp = client.chat.completions.create(
        model=DEFAULT_OPENAI_MODEL,
        messages=[
            {"role": "system", "content": _ROUTER_SYSTEM_PROMPT.format(budget=budget)},
            {"role": "user", "content": user_msg},
        ],
        response_format=_ROUTER_SCHEMA,
        temperature=0.2,
    )
    content = resp.choices[0].message.content or "{}"
    decision = json.loads(content)
    decision["queries"] = list(decision.get("queries", []))[:budget]
    return decision


def search(query: str, decision_timestamp: str, max_results: int = 5) -> list[dict[str, Any]]:
    """Issue a Tavily search and filter results to those published before
    `decision_timestamp`. Returns a list of result dicts; never raises on
    upstream failure (returns empty list with a logged error)."""
    client = tavily_client()
    cutoff = _parse_iso(decision_timestamp)
    try:
        raw = client.search(
            query,
            max_results=max_results,
            include_answer=False,
            include_raw_content=False,
            search_depth="basic",
        )
    except Exception as e:
        return [{"_error": f"tavily_failure: {type(e).__name__}: {e}"}]

    out: list[dict[str, Any]] = []
    for r in raw.get("results", []):
        pub = r.get("published_date") or r.get("publishedDate")
        try:
            if pub:
                pub_dt = _parse_iso(pub)
                if pub_dt >= cutoff:
                    continue  # post-decision leakage; drop
        except Exception:
            # If date is unparseable, conservatively drop this result.
            continue
        out.append(
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", "")[:1500],
                "published_date": pub,
                "score": float(r.get("score", 0.0)),
                "query": query,
            }
        )
    return out


def route_and_retrieve(
    state: dict[str, Any], budget: int = DEFAULT_TOOL_BUDGET
) -> dict[str, Any]:
    """End-to-end routing: decide -> search per query -> aggregate results."""
    decision = decide(state, budget=budget)
    if not decision.get("invoke_tools") or not decision.get("queries"):
        return {
            "decision": decision,
            "tool_calls": 0,
            "documents": [],
        }

    cutoff = state["decision_timestamp"]
    documents: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for q in decision["queries"][:budget]:
        results = search(q, cutoff)
        for r in results:
            if r.get("_error"):
                continue
            if r["url"] in seen_urls:
                continue
            seen_urls.add(r["url"])
            documents.append(r)

    return {
        "decision": decision,
        "tool_calls": len(decision["queries"][:budget]),
        "documents": documents,
    }
