"""Small Kalshi Trade API client with Demo RSA authentication.

Docs used:
- Demo root: https://demo-api.kalshi.co/trade-api/v2
- Auth: sign timestamp + method + path_without_query using RSA-PSS/SHA256

The client intentionally supports only the market-data and portfolio reads we
need for forecasting. It does not place trades.
"""
from __future__ import annotations

import base64
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlparse

import requests
from requests import HTTPError
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from dotenv import load_dotenv

load_dotenv()


DEMO_BASE_URL = "https://demo-api.kalshi.co/trade-api/v2"
PROD_BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"


def _load_allkeys(path: str | Path = "allkeys.txt") -> tuple[str | None, str | None]:
    """Best-effort parser for the local allkeys.txt credential dump.

    We do not print any secrets. This fallback exists because the class project
    has a local key file already, but .env-based configuration is preferred.
    """
    p = Path(path)
    if not p.exists():
        return None, None
    text = p.read_text(encoding="utf-8")
    kalshi_section = text.split("==== KALSHI KEY =====", 1)
    if len(kalshi_section) != 2:
        return None, None
    section = kalshi_section[1]
    key_id_match = re.search(
        r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
        section,
        re.IGNORECASE,
    )
    pem_match = re.search(
        r"(-----BEGIN RSA PRIVATE KEY-----.*?-----END RSA PRIVATE KEY-----)",
        section,
        re.DOTALL,
    )
    return (
        key_id_match.group(1) if key_id_match else None,
        pem_match.group(1) if pem_match else None,
    )


def _private_key_from_pem(pem: str):
    return serialization.load_pem_private_key(
        pem.encode("utf-8"),
        password=None,
        backend=default_backend(),
    )


def _sign(private_key, timestamp_ms: str, method: str, path: str) -> str:
    path_without_query = path.split("?", 1)[0]
    message = f"{timestamp_ms}{method.upper()}{path_without_query}".encode("utf-8")
    signature = private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.DIGEST_LENGTH,
        ),
        hashes.SHA256(),
    )
    return base64.b64encode(signature).decode("utf-8")


@dataclass
class KalshiClient:
    """Minimal authenticated Kalshi client for demo/prod read endpoints."""

    base_url: str = DEMO_BASE_URL
    key_id: str | None = None
    private_key_pem: str | None = None
    timeout_s: float = 20.0

    @classmethod
    def from_env(cls) -> "KalshiClient":
        env = os.getenv("KALSHI_ENV", "demo").lower()
        base_url = DEMO_BASE_URL if env == "demo" else PROD_BASE_URL
        key_id = os.getenv("KALSHI_KEY_ID") or os.getenv("KALSHI_API_KEY")
        private_key_pem = os.getenv("KALSHI_PRIVATE_KEY_PEM")
        if private_key_pem:
            private_key_pem = private_key_pem.replace("\\n", "\n")
        if not key_id or not private_key_pem:
            fallback_id, fallback_pem = _load_allkeys()
            key_id = key_id or fallback_id
            private_key_pem = private_key_pem or fallback_pem
        return cls(base_url=base_url, key_id=key_id, private_key_pem=private_key_pem)

    @property
    def is_authenticated(self) -> bool:
        return bool(self.key_id and self.private_key_pem)

    def _headers(self, method: str, endpoint_path: str) -> dict[str, str]:
        if not self.is_authenticated:
            return {}
        timestamp_ms = str(int(time.time() * 1000))
        full_path = urlparse(self.base_url + endpoint_path).path
        private_key = _private_key_from_pem(self.private_key_pem or "")
        signature = _sign(private_key, timestamp_ms, method, full_path)
        return {
            "KALSHI-ACCESS-KEY": self.key_id or "",
            "KALSHI-ACCESS-TIMESTAMP": timestamp_ms,
            "KALSHI-ACCESS-SIGNATURE": signature,
        }

    def request(self, method: str, endpoint_path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        method = method.upper()
        query = f"?{urlencode(params)}" if params else ""
        path_with_query = f"{endpoint_path}{query}"
        response = requests.request(
            method,
            self.base_url + path_with_query,
            headers=self._headers(method, endpoint_path),
            timeout=self.timeout_s,
        )
        try:
            response.raise_for_status()
        except HTTPError as exc:
            body = response.text[:1000]
            raise HTTPError(
                f"{response.status_code} {response.reason} for {response.url}: {body}"
            ) from exc
        return response.json()

    def get_balance(self) -> dict[str, Any]:
        return self.request("GET", "/portfolio/balance")

    def get_markets(
        self,
        *,
        status: str = "open",
        limit: int = 100,
        cursor: str | None = None,
        series_ticker: str | None = None,
        event_ticker: str | None = None,
        tickers: list[str] | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit}
        if status:
            params["status"] = status
        if cursor:
            params["cursor"] = cursor
        if series_ticker:
            params["series_ticker"] = series_ticker
        if event_ticker:
            params["event_ticker"] = event_ticker
        if tickers:
            params["tickers"] = ",".join(tickers)
        return self.request("GET", "/markets", params)

    def get_market(self, ticker: str) -> dict[str, Any]:
        return self.request("GET", f"/markets/{ticker}")["market"]

    def get_event(self, event_ticker: str) -> dict[str, Any]:
        return self.request("GET", f"/events/{event_ticker}")["event"]

    def get_orderbook(self, ticker: str) -> dict[str, Any]:
        return self.request("GET", f"/markets/{ticker}/orderbook")

    def get_candlesticks(
        self,
        *,
        series_ticker: str,
        ticker: str,
        start_ts: int,
        end_ts: int,
        period_interval: int = 1440,
    ) -> dict[str, Any]:
        return self.request(
            "GET",
            f"/series/{series_ticker}/markets/{ticker}/candlesticks",
            {
                "start_ts": start_ts,
                "end_ts": end_ts,
                "period_interval": period_interval,
                "include_latest_before_start": "true",
            },
        )

