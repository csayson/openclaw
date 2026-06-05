"""
F1 — Earnings Surprise Momentum
Trades post-earnings price reactions based on EPS surprise magnitude.
"""
from __future__ import annotations
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any
import structlog

from app.strategies.base import BaseStrategy, StrategySignal

log = structlog.get_logger()

MIN_SURPRISE_PCT = 5.0
MIN_FINBERT_SCORE = 0.65
MIN_MARKET_CAP = 2e9
MIN_AVG_VOLUME = 1_000_000
MAX_IV_RANK = 80
HOLD_DAYS = (3, 5)


class EarningsSurpriseStrategy(BaseStrategy):
    name = "EarningsSurprise"
    strategy_type = "FUNDAMENTAL"

    async def scan(self, instruments: list[str], market_data: Any) -> list[StrategySignal]:
        signals: list[StrategySignal] = []
        upcoming = await self._get_upcoming_earnings(instruments, days_ahead=7)

        for ticker in upcoming:
            try:
                sig = await self._evaluate_ticker(ticker, market_data)
                if sig:
                    signals.append(sig)
            except Exception as e:
                log.warning("f1_eval_error", ticker=ticker, error=str(e))
        return signals

    async def _evaluate_ticker(self, ticker: str, market_data: Any) -> StrategySignal | None:
        meta = await market_data.get_fundamentals(ticker)
        if meta.get("market_cap", 0) < MIN_MARKET_CAP:
            return None
        if meta.get("avg_volume", 0) < MIN_AVG_VOLUME:
            return None
        if meta.get("iv_rank", 0) > MAX_IV_RANK:
            return None

        earnings = await market_data.get_latest_earnings(ticker)
        if not earnings:
            return None

        actual_eps = earnings.get("actual_eps", 0)
        estimate_eps = earnings.get("estimate_eps", 1)
        if estimate_eps == 0:
            return None
        surprise_pct = ((actual_eps - estimate_eps) / abs(estimate_eps)) * 100

        if abs(surprise_pct) < MIN_SURPRISE_PCT:
            return None

        # FinBERT sentiment on transcript must confirm
        transcript = await market_data.get_earnings_transcript(ticker)
        sentiment_score = await market_data.finbert_sentiment(transcript)
        direction = "LONG" if surprise_pct > 0 else "SHORT"
        sentiment_ok = (
            (direction == "LONG" and sentiment_score > MIN_FINBERT_SCORE)
            or (direction == "SHORT" and sentiment_score < -MIN_FINBERT_SCORE)
        )
        if not sentiment_ok:
            return None

        price = await market_data.get_current_price(ticker)
        atr = await market_data.get_atr(ticker, period=14)
        entry = price
        sl = entry - atr * 1.5 if direction == "LONG" else entry + atr * 1.5
        tp = entry + atr * 3.0 if direction == "LONG" else entry - atr * 3.0

        # IV-adjusted position scaling handled by risk manager
        confidence = min(1.0, (abs(surprise_pct) / 20) * abs(sentiment_score))

        return StrategySignal(
            instrument=ticker,
            direction=direction,
            entry_price=entry,
            stop_loss=sl,
            take_profit=tp,
            lot_size=0.0,  # sized by risk manager
            confidence_score=confidence,
            strategy=self.name,
            strategy_type=self.strategy_type,
            filters_passed=["EPS_SURPRISE", "MARKET_CAP", "VOLUME", "FINBERT", "IV_RANK"],
            notes=f"EPS surprise {surprise_pct:.1f}%, FinBERT {sentiment_score:.2f}",
        )

    async def _get_upcoming_earnings(self, instruments: list[str], days_ahead: int) -> list[str]:
        # In production: query yfinance / earnings calendar API
        return instruments
