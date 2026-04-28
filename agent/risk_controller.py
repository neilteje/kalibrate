"""Risk Controller.

Pure-Python decision logic that decides whether to abstain from a forecast
or commit to one. Abstention is implemented as outputting p=0.5 (a neutral
forecast yielding Brier=0.25 on a binary outcome). The controller fires
when any of the following hold:

  1. Self-reported confidence is below `tau_abs`.
  2. Volatility proxy exceeds `vol_abs_threshold` (a high-volatility regime).
  3. No retrieved evidence reaches a minimum relevance bar.

When the controller does not abstain, it returns the (clipped) p_hat as the
final probability.
"""
from __future__ import annotations

from typing import Any


DEFAULT_TAU_ABS = 0.35
DEFAULT_VOL_ABS_THRESHOLD = 0.055
DEFAULT_MIN_RELEVANCE = 0.40


def decide(
    forecast: dict[str, Any],
    state: dict[str, Any],
    evidence: dict[str, Any] | None = None,
    *,
    tau_abs: float = DEFAULT_TAU_ABS,
    vol_threshold: float = DEFAULT_VOL_ABS_THRESHOLD,
    min_relevance: float = DEFAULT_MIN_RELEVANCE,
) -> dict[str, Any]:
    """Apply abstention logic. Returns a dict with `abstain`, `p_final`, and
    a list of reasons for the decision."""
    reasons: list[str] = []

    confidence = float(forecast.get("confidence", 0.5))
    if confidence < tau_abs:
        reasons.append(f"low_confidence({confidence:.2f}<{tau_abs:.2f})")

    vol = float(state.get("volatility_proxy", 0.0))
    if vol > vol_threshold:
        reasons.append(f"high_volatility({vol:.3f}>{vol_threshold:.3f})")

    if evidence is not None and evidence.get("per_document"):
        max_rel = float(evidence.get("aggregate", {}).get("max_relevance", 0.0))
        if max_rel < min_relevance:
            reasons.append(f"low_evidence_relevance(max={max_rel:.2f})")

    abstain = len(reasons) > 0
    p_final = 0.5 if abstain else float(forecast["p_hat"])
    return {
        "abstain": abstain,
        "p_final": p_final,
        "reasons": reasons,
    }
