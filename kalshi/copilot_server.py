"""Local HTTP bridge for the Kalshi Demo browser copilot overlay.

Run:
    python3 -m kalshi.copilot_server --port 8765 --tool-budget 1

The browser extension calls this service from the Kalshi demo page, sending
the currently visible market ticker/title. The service returns a KALIBRATE
forecast JSON payload suitable for quick in-page display.
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import time
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from kalshi.client import KalshiClient
from kalshi.forecast import forecast_live_state
from kalshi.live_state import build_live_market_state, list_candidate_markets


def _slugify(value: str, default: str = "web-market") -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or default


def _synthetic_state(*, title: str, context_hint: str, ticker: str | None = None) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    resolution = now + timedelta(days=7)
    clean_ticker = ticker or _slugify(title).upper()
    return {
        "task_id": clean_ticker,
        "title": title or clean_ticker,
        "domain": "kalshi_live_web",
        "resolution_criteria": "Derived from visible Kalshi Demo page content.",
        "decision_timestamp": now.isoformat().replace("+00:00", "Z"),
        "resolution_timestamp": resolution.isoformat().replace("+00:00", "Z"),
        "time_to_resolution_hours": 7 * 24.0,
        "price_history": [0.5],
        "volatility_proxy": 0.0,
        "liquidity_proxy": 0.5,
        "context_hint": context_hint,
    }


def _best_title_match_ticker(client: KalshiClient, title: str) -> str | None:
    """Resolve a likely Kalshi ticker from a messy page title."""
    cleaned = " ".join((title or "").split())
    if not cleaned:
        return None
    try:
        candidates = list_candidate_markets(client, limit=200, query=cleaned[:40])
        if len(candidates) < 5:
            # Query sometimes over-filters. Fall back to broad open markets.
            candidates = list_candidate_markets(client, limit=200, query=None)
    except Exception:
        return None
    if not candidates:
        return None

    best_ticker: str | None = None
    best_score = 0.0
    probe = re.sub(r"[^a-z0-9 ]+", " ", cleaned.lower())
    for market in candidates:
        m_title = market.get("title") or ""
        m_sub = market.get("yes_sub_title") or ""
        hay = f"{m_title} {m_sub}".strip().lower()
        hay_norm = re.sub(r"[^a-z0-9 ]+", " ", hay)
        score = difflib.SequenceMatcher(a=probe, b=hay_norm).ratio()
        if score > best_score:
            best_score = score
            best_ticker = market.get("ticker")
    return best_ticker if best_score >= 0.45 else None


def _predict_market(
    *,
    client: KalshiClient,
    ticker: str | None,
    title: str | None,
    tool_budget: int,
    commit_even_if_risky: bool,
    page_context: str | None,
) -> dict[str, Any]:
    resolved_ticker = ticker
    if not resolved_ticker and title:
        resolved_ticker = _best_title_match_ticker(client, title)

    if resolved_ticker:
        try:
            state = build_live_market_state(client, resolved_ticker)
            result = forecast_live_state(
                state,
                tool_budget=tool_budget,
                commit_even_if_risky=commit_even_if_risky,
            )
            result["source"] = "kalshi_api_title_match" if not ticker else "kalshi_api"
            result["resolved_ticker"] = resolved_ticker
            return result
        except Exception as exc:
            fallback_context = (
                f"Ticker lookup failed for {resolved_ticker}: {exc}. "
                f"Page context: {page_context or '(none)'}"
            )
            state = _synthetic_state(
                title=title or resolved_ticker,
                ticker=resolved_ticker,
                context_hint=fallback_context,
            )
            result = forecast_live_state(
                state,
                tool_budget=tool_budget,
                commit_even_if_risky=commit_even_if_risky,
            )
            result["source"] = "page_fallback"
            result["lookup_error"] = str(exc)
            return result

    state = _synthetic_state(
        title=title or "Unknown Kalshi market",
        context_hint=(
            f"Forecast from visible page content only. Page context: {page_context or '(none)'}"
        ),
    )
    result = forecast_live_state(
        state,
        tool_budget=tool_budget,
        commit_even_if_risky=commit_even_if_risky,
    )
    result["source"] = "page_only"
    return result


def make_handler(
    *,
    client: KalshiClient,
    default_tool_budget: int,
    default_commit_even_if_risky: bool,
) -> type[BaseHTTPRequestHandler]:
    class CopilotHandler(BaseHTTPRequestHandler):
        def _send_json(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
            self.wfile.write(body)

        def do_OPTIONS(self) -> None:  # noqa: N802
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()

        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/health":
                self._send_json(
                    200,
                    {
                        "ok": True,
                        "service": "kalshi-copilot",
                        "ts": int(time.time()),
                    },
                )
                return
            self._send_json(404, {"ok": False, "error": "Not found"})

        def do_POST(self) -> None:  # noqa: N802
            if self.path != "/forecast":
                self._send_json(404, {"ok": False, "error": "Not found"})
                return
            try:
                raw_length = int(self.headers.get("Content-Length", "0"))
                payload_raw = self.rfile.read(raw_length) if raw_length > 0 else b"{}"
                payload = json.loads(payload_raw.decode("utf-8"))
                ticker = payload.get("ticker") or None
                title = payload.get("title") or None
                page_context = payload.get("page_context") or None
                tool_budget = int(payload.get("tool_budget", default_tool_budget))
                commit_even_if_risky = bool(
                    payload.get("commit_even_if_risky", default_commit_even_if_risky)
                )
                result = _predict_market(
                    client=client,
                    ticker=ticker,
                    title=title,
                    tool_budget=tool_budget,
                    commit_even_if_risky=commit_even_if_risky,
                    page_context=page_context,
                )
                self._send_json(200, {"ok": True, "result": result})
            except Exception as exc:
                self._send_json(500, {"ok": False, "error": str(exc)})

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
            return

    return CopilotHandler


def main() -> None:
    parser = argparse.ArgumentParser(description="Local Kalshi Copilot API bridge.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host, default 127.0.0.1.")
    parser.add_argument("--port", type=int, default=8765, help="Bind port, default 8765.")
    parser.add_argument("--tool-budget", type=int, default=1, help="Default Tavily calls per request.")
    parser.add_argument(
        "--abstain",
        action="store_true",
        help="Use risk-controller abstention as the final prediction.",
    )
    args = parser.parse_args()

    client = KalshiClient.from_env()
    handler = make_handler(
        client=client,
        default_tool_budget=args.tool_budget,
        default_commit_even_if_risky=not args.abstain,
    )
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Kalshi Copilot bridge listening on http://{args.host}:{args.port}")
    print("Endpoints: GET /health, POST /forecast")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
