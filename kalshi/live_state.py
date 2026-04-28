"""Convert live Kalshi markets into KALIBRATE market states."""
from __future__ import annotations

import statistics
import time
from datetime import datetime, timezone
from typing import Any

from .client import KalshiClient


def _to_float(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _midpoint(market: dict[str, Any]) -> float:
    yes_bid = _to_float(market.get("yes_bid_dollars"), 0.0)
    yes_ask = _to_float(market.get("yes_ask_dollars"), 0.0)
    last = _to_float(market.get("last_price_dollars"), 0.0)
    vals = [v for v in [yes_bid, yes_ask] if v > 0]
    if len(vals) == 2:
        return (vals[0] + vals[1]) / 2
    if last > 0:
        return last
    return yes_bid or yes_ask or 0.5


def _extract_price_history(candlesticks: list[dict[str, Any]]) -> list[float]:
    prices: list[float] = []
    for candle in candlesticks:
        price = candle.get("price") or {}
        val = (
            price.get("close_dollars")
            or price.get("mean_dollars")
            or price.get("previous_dollars")
        )
        if val not in (None, ""):
            prices.append(_to_float(val))
    return prices[-7:]


def _volatility(prices: list[float]) -> float:
    if len(prices) < 2:
        return 0.0
    deltas = [b - a for a, b in zip(prices, prices[1:])]
    return statistics.pstdev(deltas) if len(deltas) > 1 else abs(deltas[0])


def _liquidity_proxy(market: dict[str, Any]) -> float:
    volume = _to_float(market.get("volume_fp"), 0.0)
    oi = _to_float(market.get("open_interest_fp"), 0.0)
    # Saturating transform: 0 contracts -> 0, thousands of contracts -> close to 1.
    return min(1.0, (volume + oi) / 5000.0)


def build_live_market_state(
    client: KalshiClient,
    ticker: str,
    *,
    lookback_days: int = 7,
    period_interval: int = 1440,
) -> dict[str, Any]:
    """Fetch a live Kalshi market and return an agent-visible market state."""
    market = client.get_market(ticker)
    event = client.get_event(market["event_ticker"])
    now = datetime.now(timezone.utc)
    close_time = market.get("close_time") or market.get("latest_expiration_time")

    end_ts = int(time.time())
    start_ts = end_ts - lookback_days * 86400
    candlesticks: list[dict[str, Any]] = []
    try:
        series_ticker = market["event_ticker"].split("-")[0]
        # Most Kalshi event tickers begin with the series ticker. If this
        # inference fails, the fallback price history below still works.
        raw = client.get_candlesticks(
            series_ticker=series_ticker,
            ticker=market["ticker"],
            start_ts=start_ts,
            end_ts=end_ts,
            period_interval=period_interval,
        )
        candlesticks = raw.get("candlesticks", [])
    except Exception:
        candlesticks = []

    price_history = _extract_price_history(candlesticks)
    if not price_history:
        previous = _to_float(market.get("previous_price_dollars"), 0.0)
        midpoint = _midpoint(market)
        price_history = [p for p in [previous, midpoint] if p > 0]
    if not price_history:
        price_history = [0.5]

    try:
        close_dt = datetime.fromisoformat(close_time.replace("Z", "+00:00"))
        time_to_resolution_hours = max(0.0, (close_dt - now).total_seconds() / 3600.0)
    except Exception:
        time_to_resolution_hours = 0.0

    base_title = market.get("title") or event.get("title") or ticker
    yes_sub_title = market.get("yes_sub_title")
    title = f"{base_title} YES: {yes_sub_title}" if yes_sub_title else base_title
    rules_primary = market.get("rules_primary") or ""
    rules_secondary = market.get("rules_secondary") or ""

    return {
        "task_id": ticker,
        "title": title,
        "domain": event.get("category", "kalshi_live"),
        "resolution_criteria": "\n".join(x for x in [rules_primary, rules_secondary] if x).strip(),
        "decision_timestamp": now.isoformat().replace("+00:00", "Z"),
        "resolution_timestamp": close_time,
        "time_to_resolution_hours": time_to_resolution_hours,
        "price_history": price_history,
        "volatility_proxy": _volatility(price_history),
        "liquidity_proxy": _liquidity_proxy(market),
        "context_hint": (
            f"Kalshi live demo market {market['ticker']} in event {market['event_ticker']}. "
            f"YES bid/ask={market.get('yes_bid_dollars')}/{market.get('yes_ask_dollars')}; "
            f"NO bid/ask={market.get('no_bid_dollars')}/{market.get('no_ask_dollars')}; "
            f"last traded YES price={market.get('last_price_dollars')}; "
            f"volume={market.get('volume_fp')}; open interest={market.get('open_interest_fp')}."
        ),
        "kalshi_market": market,
        "kalshi_event": event,
    }


def list_candidate_markets(
    client: KalshiClient,
    *,
    limit: int = 25,
    status: str = "open",
    query: str | None = None,
) -> list[dict[str, Any]]:
    """Return open markets, optionally keyword-filtered by title/subtitle."""
    data = client.get_markets(status=status, limit=limit)
    markets = data.get("markets", [])
    if query:
        q = query.lower()
        markets = [
            m
            for m in markets
            if q in (m.get("title") or "").lower()
            or q in (m.get("yes_sub_title") or "").lower()
            or q in (m.get("event_ticker") or "").lower()
        ]
    return markets

