"""B3: Tool-enabled frontier model baseline.

GPT-4o with function-calling access to a `web_search` tool that wraps
Tavily under the hood (with the same temporal-cutoff filtering as the
KALIBRATE agent, for fair comparison). No custom evidence extractor,
no risk controller, no schema-constrained intermediate planning. Tests
whether KALIBRATE's structured pipeline beats a strong off-the-shelf
agentic baseline given the same retrieval primitive and budget.
"""
from __future__ import annotations

import json
import time
from typing import Any

from agent import market_state
from agent.forecaster import P_CEIL, P_FLOOR
from agent.llm_clients import DEFAULT_OPENAI_FRONTIER, openai_client
from agent.tool_router import search as tavily_search


SYSTEM_NAME = "frontier_tool"
TOOL_BUDGET = 3


_SYSTEM_PROMPT = f"""You are a probabilistic forecaster with access to a \
web_search tool. You may call web_search up to {TOOL_BUDGET} times to \
retrieve evidence. The tool ONLY returns results published before the \
market's decision_timestamp; you cannot circumvent this.

When you are ready to answer, output your final forecast as a JSON object \
in your final assistant message with these fields:
- p_hat: float in [{P_FLOOR}, {P_CEIL}]
- confidence: float in [0, 1]
- signals_used: list of short strings
- reasoning_summary: at most 2 sentences

Do not output the final forecast until you have stopped calling tools."""


_TOOL_DEFS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Search the web for evidence. Returns up to 5 results, all "
                "published before the market's decision_timestamp."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                },
                "required": ["query"],
            },
        },
    }
]


def _final_forecast_schema():
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "FinalForecast",
            "strict": True,
            "schema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "p_hat": {"type": "number", "minimum": 0, "maximum": 1},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "signals_used": {"type": "array", "items": {"type": "string"}},
                    "reasoning_summary": {"type": "string"},
                },
                "required": ["p_hat", "confidence", "signals_used", "reasoning_summary"],
            },
        },
    }


def _format_search_results(results: list[dict[str, Any]]) -> str:
    if not results:
        return json.dumps({"results": [], "note": "no_pre_cutoff_results"})
    return json.dumps(
        {
            "results": [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "published_date": r.get("published_date"),
                    "content": r.get("content", "")[:800],
                }
                for r in results
                if not r.get("_error")
            ]
        }
    )


def run(
    task: dict[str, Any],
    model: str = DEFAULT_OPENAI_FRONTIER,
    temperature: float = 0.3,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    state = market_state.build_state(task)
    cutoff = state["decision_timestamp"]
    client = openai_client()

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps({"market_state": state})},
    ]

    tool_calls_used = 0
    documents_retrieved = 0
    max_iterations = TOOL_BUDGET + 2

    for _ in range(max_iterations):
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if tool_calls_used < TOOL_BUDGET:
            kwargs["tools"] = _TOOL_DEFS
            kwargs["tool_choice"] = "auto"
        else:
            # Force structured final answer when budget is exhausted.
            kwargs["response_format"] = _final_forecast_schema()

        resp = client.chat.completions.create(**kwargs)
        msg = resp.choices[0].message

        if getattr(msg, "tool_calls", None):
            messages.append(
                {
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in msg.tool_calls
                    ],
                }
            )
            for tc in msg.tool_calls:
                if tc.function.name != "web_search":
                    tool_result = json.dumps({"error": "unknown_tool"})
                else:
                    args = json.loads(tc.function.arguments or "{}")
                    query = args.get("query", "")
                    results = tavily_search(query, cutoff)
                    documents_retrieved += sum(1 for r in results if not r.get("_error"))
                    tool_result = _format_search_results(results)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": tool_result,
                    }
                )
                tool_calls_used += 1
            continue

        # No more tool calls; this should be the final structured answer.
        content = msg.content or "{}"
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            # One more call enforcing schema.
            messages.append({"role": "assistant", "content": content})
            messages.append(
                {
                    "role": "user",
                    "content": "Please output your final forecast as a JSON object now.",
                }
            )
            resp2 = client.chat.completions.create(
                model=model,
                messages=messages,
                response_format=_final_forecast_schema(),
                temperature=temperature,
            )
            parsed = json.loads(resp2.choices[0].message.content or "{}")
        break
    else:
        parsed = {
            "p_hat": 0.5,
            "confidence": 0.0,
            "signals_used": [],
            "reasoning_summary": "Failed to converge within iteration limit.",
        }

    p_hat = max(P_FLOOR, min(P_CEIL, float(parsed.get("p_hat", 0.5))))
    return {
        "task_id": task["task_id"],
        "system": SYSTEM_NAME,
        "p_final": p_hat,
        "p_hat_raw": p_hat,
        "abstain": False,
        "abstain_reasons": [],
        "confidence": float(parsed.get("confidence", 0.5)),
        "tool_calls": tool_calls_used,
        "documents_retrieved": documents_retrieved,
        "forecast_reasoning": parsed.get("reasoning_summary", ""),
        "signals_used": parsed.get("signals_used", []),
        "runtime_s": round(time.perf_counter() - t0, 3),
    }
