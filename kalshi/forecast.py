"""CLI for running KALIBRATE against live Kalshi Demo markets.

Examples:
    python3 -m kalshi.forecast --balance
    python3 -m kalshi.forecast --list --limit 10
    python3 -m kalshi.forecast --ticker KXHIGHNY-25APR28-T70
    python3 -m kalshi.forecast --query oscars --limit 5
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent import evidence_extractor, forecaster, risk_controller, tool_router  # noqa: E402
from kalshi.client import KalshiClient  # noqa: E402
from kalshi.live_state import build_live_market_state, list_candidate_markets  # noqa: E402


def _format_market(m: dict[str, Any]) -> str:
    title = m.get("title") or m.get("yes_sub_title") or ""
    yes = m.get("yes_bid_dollars") or "?"
    no = m.get("no_bid_dollars") or "?"
    vol = m.get("volume_fp") or "0"
    return f"{m['ticker']:34s} yes_bid={yes:>7s} no_bid={no:>7s} vol={vol:>10s}  {title}"


def forecast_live_state(
    state: dict[str, Any],
    *,
    tool_budget: int = 3,
    commit_even_if_risky: bool = True,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    if tool_budget > 0:
        retrieval = tool_router.route_and_retrieve(state, budget=tool_budget)
    else:
        retrieval = {"decision": {"invoke_tools": False, "queries": []}, "tool_calls": 0, "documents": []}
    evidence = evidence_extractor.extract(state, retrieval["documents"]) if retrieval["documents"] else None
    fc = forecaster.forecast(state, evidence=evidence)
    risk = risk_controller.decide(fc, state, evidence)
    p_final = fc["p_hat"] if commit_even_if_risky else risk["p_final"]
    return {
        "ticker": state["task_id"],
        "title": state["title"],
        "p_final": p_final,
        "p_hat_raw": fc["p_hat"],
        "confidence": fc["confidence"],
        "risk_flag": risk["abstain"],
        "risk_reasons": risk["reasons"],
        "tool_calls": retrieval["tool_calls"],
        "documents_retrieved": len(retrieval["documents"]),
        "router_decision": retrieval["decision"],
        "evidence_summary": (evidence or {}).get("aggregate"),
        "reasoning_summary": fc["reasoning_summary"],
        "signals_used": fc["signals_used"],
        "runtime_s": round(time.perf_counter() - t0, 3),
        "market_state": {
            k: v
            for k, v in state.items()
            if k not in {"kalshi_market", "kalshi_event"}
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Forecast live Kalshi Demo markets with KALIBRATE.")
    parser.add_argument("--balance", action="store_true", help="Check authenticated demo balance.")
    parser.add_argument("--list", action="store_true", help="List candidate open markets.")
    parser.add_argument("--ticker", type=str, help="Forecast a specific Kalshi market ticker.")
    parser.add_argument("--query", type=str, help="Keyword filter for --list or batch forecasting.")
    parser.add_argument("--limit", type=int, default=10, help="Number of markets to list/fetch.")
    parser.add_argument("--tool-budget", type=int, default=3, help="Tavily calls per forecast.")
    parser.add_argument("--json", action="store_true", help="Print raw JSON output.")
    parser.add_argument(
        "--abstain",
        action="store_true",
        help="Use risk-controller abstention as the final probability (otherwise still show risk flag, but commit to p_hat).",
    )
    args = parser.parse_args()

    client = KalshiClient.from_env()

    if args.balance:
        balance = client.get_balance()
        dollars = balance.get("balance", 0) / 100
        portfolio = balance.get("portfolio_value", 0) / 100
        print(f"Demo balance: ${dollars:,.2f} | portfolio value: ${portfolio:,.2f}")

    if args.list or (not args.ticker and not args.balance):
        markets = list_candidate_markets(client, limit=args.limit, query=args.query)
        print(f"Open Kalshi Demo markets ({len(markets)} shown):")
        for m in markets:
            print("  " + _format_market(m))
        if not args.ticker:
            return

    if args.ticker:
        state = build_live_market_state(client, args.ticker)
        result = forecast_live_state(
            state,
            tool_budget=args.tool_budget,
            commit_even_if_risky=not args.abstain,
        )
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            print("\nKALIBRATE live forecast")
            print("=" * 80)
            print(f"Ticker     : {result['ticker']}")
            print(f"Title      : {result['title']}")
            print(f"Forecast   : YES probability = {result['p_final']:.3f}")
            print(f"Confidence : {result['confidence']:.3f}")
            print(f"Risk flag  : {result['risk_flag']} {result['risk_reasons']}")
            print(f"Tools      : {result['tool_calls']} calls, {result['documents_retrieved']} docs")
            print(f"Reasoning  : {result['reasoning_summary']}")
            print(f"Runtime    : {result['runtime_s']}s")


if __name__ == "__main__":
    main()

