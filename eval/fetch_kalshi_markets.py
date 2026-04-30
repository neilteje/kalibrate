"""Fetch real Kalshi Demo market data and enrich POPCAST task files.

This script:
1. Pulls ALL open markets from the Kalshi Demo API (paginated)
2. For each market with volume > 0, fetches orderbook depth
3. Computes real spread/liquidity/volume statistics
4. Enriches each POPCAST task with a `kalshi_api_context` block
   containing real API-sourced market intelligence
5. Saves a raw API snapshot for reproducibility

Usage:
    python eval/fetch_kalshi_markets.py [--output-dir results/kalshi_snapshots]
"""
from __future__ import annotations

import json
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from kalshi.client import KalshiClient  # noqa: E402


def _retry_request(fn, *args, max_retries: int = 3, **kwargs):
    for attempt in range(max_retries):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            if "429" in str(exc) or "Too Many" in str(exc):
                wait = 2 ** (attempt + 1)
                print(f"       Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            raise
    return fn(*args, **kwargs)


def fetch_all_open_markets(client: KalshiClient, max_pages: int = 10) -> list[dict]:
    all_markets: list[dict] = []
    cursor = None
    for _ in range(max_pages):
        data = _retry_request(client.get_markets, status="open", limit=100, cursor=cursor)
        batch = data.get("markets", [])
        all_markets.extend(batch)
        cursor = data.get("cursor")
        if not cursor or not batch:
            break
        time.sleep(0.3)
    return all_markets


def fetch_orderbooks(client: KalshiClient, tickers: list[str]) -> dict[str, dict]:
    orderbooks: dict[str, dict] = {}
    for ticker in tickers:
        try:
            ob = _retry_request(client.get_orderbook, ticker)
            orderbooks[ticker] = ob
        except Exception:
            continue
        time.sleep(0.2)
    return orderbooks


def compute_market_statistics(markets: list[dict], orderbooks: dict) -> dict[str, Any]:
    """Compute aggregate statistics across all fetched markets."""
    volumes = [float(m.get("volume_fp") or 0) for m in markets]
    open_interests = [float(m.get("open_interest_fp") or 0) for m in markets]
    spreads = []
    for m in markets:
        yb = float(m.get("yes_bid_dollars") or 0)
        ya = float(m.get("yes_ask_dollars") or 0)
        if yb > 0 and ya > 0 and ya > yb:
            spreads.append(ya - yb)

    active_markets = [m for m in markets if float(m.get("volume_fp") or 0) > 0]
    depths = []
    for ticker, ob in orderbooks.items():
        fp = ob.get("orderbook_fp", {})
        yes_levels = len(fp.get("yes_dollars", []))
        no_levels = len(fp.get("no_dollars", []))
        depths.append(yes_levels + no_levels)

    def safe_stats(vals):
        if not vals:
            return {"mean": 0, "median": 0, "std": 0, "min": 0, "max": 0, "count": 0}
        return {
            "mean": round(statistics.mean(vals), 4),
            "median": round(statistics.median(vals), 4),
            "std": round(statistics.pstdev(vals), 4) if len(vals) > 1 else 0,
            "min": round(min(vals), 4),
            "max": round(max(vals), 4),
            "count": len(vals),
        }

    return {
        "total_markets_fetched": len(markets),
        "active_markets": len(active_markets),
        "orderbooks_fetched": len(orderbooks),
        "volume_stats": safe_stats(volumes),
        "open_interest_stats": safe_stats(open_interests),
        "spread_stats": safe_stats(spreads),
        "orderbook_depth_stats": safe_stats(depths),
    }


def build_enrichment_context(
    markets: list[dict], stats: dict, orderbooks: dict
) -> dict[str, Any]:
    """Build the kalshi_api_context block to inject into POPCAST tasks."""
    active = sorted(
        [m for m in markets if float(m.get("volume_fp") or 0) > 0],
        key=lambda m: -float(m.get("volume_fp") or 0),
    )
    sample_markets = []
    for m in active[:15]:
        ticker = m["ticker"]
        ob = orderbooks.get(ticker, {}).get("orderbook_fp", {})
        yes_depth = sum(float(lvl[1]) for lvl in ob.get("yes_dollars", []))
        no_depth = sum(float(lvl[1]) for lvl in ob.get("no_dollars", []))
        sample_markets.append({
            "ticker": ticker,
            "title": m.get("title", ""),
            "yes_bid": m.get("yes_bid_dollars"),
            "yes_ask": m.get("yes_ask_dollars"),
            "no_bid": m.get("no_bid_dollars"),
            "no_ask": m.get("no_ask_dollars"),
            "volume": float(m.get("volume_fp") or 0),
            "open_interest": float(m.get("open_interest_fp") or 0),
            "orderbook_yes_depth": yes_depth,
            "orderbook_no_depth": no_depth,
            "close_time": m.get("close_time"),
            "event_ticker": m.get("event_ticker"),
        })
    return {
        "api_fetch_timestamp": datetime.now(timezone.utc).isoformat(),
        "api_base_url": "https://demo-api.kalshi.co/trade-api/v2",
        "aggregate_statistics": stats,
        "sample_active_markets": sample_markets,
    }


def enrich_task(task: dict, api_context: dict) -> dict:
    """Add kalshi_api_context to a task without modifying existing fields."""
    enriched = dict(task)
    enriched["kalshi_api_context"] = api_context
    return enriched


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Fetch Kalshi market data for POPCAST.")
    parser.add_argument("--output-dir", default=str(ROOT / "results" / "kalshi_snapshots"))
    parser.add_argument("--enrich-tasks", action="store_true", default=True,
                        help="Write enriched task files to output dir.")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    client = KalshiClient.from_env()
    print(f"Kalshi client: authenticated={client.is_authenticated}, base={client.base_url}")

    print("\n[1/4] Fetching all open markets...")
    markets = fetch_all_open_markets(client)
    print(f"       Fetched {len(markets)} open markets")

    active_tickers = [
        m["ticker"] for m in markets if float(m.get("volume_fp") or 0) > 0
    ]
    print(f"\n[2/4] Fetching orderbooks for {len(active_tickers)} active markets...")
    orderbooks = fetch_orderbooks(client, active_tickers)
    print(f"       Got {len(orderbooks)} orderbooks")

    print("\n[3/4] Computing market statistics...")
    stats = compute_market_statistics(markets, orderbooks)
    print(f"       Total: {stats['total_markets_fetched']} markets, "
          f"{stats['active_markets']} active, "
          f"median volume: {stats['volume_stats']['median']}")

    api_context = build_enrichment_context(markets, stats, orderbooks)

    snapshot_path = output_dir / "api_snapshot.json"
    with snapshot_path.open("w", encoding="utf-8") as f:
        json.dump({
            "fetch_timestamp": api_context["api_fetch_timestamp"],
            "statistics": stats,
            "active_markets": api_context["sample_active_markets"],
            "all_market_tickers": [m["ticker"] for m in markets],
            "orderbooks": {
                t: ob for t, ob in list(orderbooks.items())[:20]
            },
        }, f, indent=2, default=str)
    print(f"       Saved raw snapshot: {snapshot_path}")

    print("\n[4/4] Enriching POPCAST task files...")
    tasks_dir = ROOT / "tasks"
    enriched_dir = output_dir / "enriched_tasks"
    enriched_dir.mkdir(parents=True, exist_ok=True)

    for task_path in sorted(tasks_dir.glob("T*.json")):
        with task_path.open("r", encoding="utf-8") as f:
            task = json.load(f)
        enriched = enrich_task(task, api_context)
        out_path = enriched_dir / task_path.name
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(enriched, f, indent=2, default=str)
        print(f"       {task_path.name} -> {out_path.name} "
              f"(+kalshi_api_context with {len(api_context['sample_active_markets'])} real markets)")

    print(f"\nDone. All outputs in {output_dir}/")
    print("\nAPI Statistics Summary:")
    print(f"  Markets fetched:     {stats['total_markets_fetched']}")
    print(f"  Active (volume>0):   {stats['active_markets']}")
    print(f"  Orderbooks fetched:  {stats['orderbooks_fetched']}")
    print(f"  Volume range:        {stats['volume_stats']['min']:.0f} - {stats['volume_stats']['max']:.0f}")
    print(f"  Spread median:       {stats['spread_stats']['median']:.4f}")
    print(f"  OB depth median:     {stats['orderbook_depth_stats']['median']:.1f} levels")


if __name__ == "__main__":
    main()
