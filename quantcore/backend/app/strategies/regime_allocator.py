"""
Market regime detection and strategy weight allocation.
Regime is determined by VIX level, ADX trend strength, and rolling returns.
"""
from __future__ import annotations
import structlog

log = structlog.get_logger()

REGIME_WEIGHTS: dict[str, dict[str, float]] = {
    "TRENDING_BULL": {
        "MomentumBreakout": 0.25,
        "MacroTrendFollow": 0.20,
        "FundamentalValue": 0.20,
        "EarningsSurprise": 0.15,
        "InsiderSignal": 0.10,
        "ThetaDecay": 0.10,
    },
    "RANGING_LOW_VOL": {
        "MeanReversionPairs": 0.30,
        "ThetaDecay": 0.25,
        "DividendCapture": 0.20,
        "SentimentFlow": 0.15,
        "MacroCalendar": 0.10,
    },
    "HIGH_VOL_CRISIS": {
        "MacroCalendar": 0.35,
        "MeanReversionPairs": 0.25,
        "SentimentFlow": 0.20,
        "Cash": 0.20,
    },
    "RECOVERY": {
        "FundamentalValue": 0.30,
        "EarningsSurprise": 0.25,
        "InsiderSignal": 0.20,
        "MomentumBreakout": 0.15,
        "DividendCapture": 0.10,
    },
}


def allocate_strategy_weights(market_regime: str) -> dict[str, float]:
    return REGIME_WEIGHTS.get(market_regime, REGIME_WEIGHTS["RANGING_LOW_VOL"])


def detect_regime(vix: float, adx: float, spy_return_20d: float) -> str:
    """
    Simple heuristic regime classifier.
    Production: replace with ML classifier trained on labeled regimes.
    """
    if vix > 30:
        return "HIGH_VOL_CRISIS"
    if vix < 18 and adx > 25 and spy_return_20d > 0:
        return "TRENDING_BULL"
    if vix < 18 and adx < 20:
        return "RANGING_LOW_VOL"
    if spy_return_20d > -0.05 and vix < 25:
        return "RECOVERY"
    return "RANGING_LOW_VOL"
