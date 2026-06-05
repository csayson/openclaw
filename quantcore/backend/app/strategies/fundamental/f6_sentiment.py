"""
F6 — Sentiment & News Flow Alpha
Extracts alpha from NLP analysis of news, analyst upgrades, and social sentiment.
"""
from __future__ import annotations
from typing import Any
import structlog
from app.strategies.base import BaseStrategy, StrategySignal

log = structlog.get_logger()

LONG_SENTIMENT_THRESHOLD = 0.75
SHORT_SENTIMENT_THRESHOLD = -0.75
NEUTRAL_MEAN_REVERT = 0.3
MIN_PUT_CALL_RATIO_SHORT = 1.5
ROLLING_WINDOW_HOURS = 4
ANALYST_UPGRADE_BONUS = 25


class SentimentFlowStrategy(BaseStrategy):
    name = "SentimentFlow"
    strategy_type = "FUNDAMENTAL"

    async def scan(self, instruments: list[str], market_data: Any) -> list[StrategySignal]:
        signals: list[StrategySignal] = []
        for ticker in instruments:
            try:
                sig = await self._evaluate(ticker, market_data)
                if sig:
                    signals.append(sig)
            except Exception as e:
                log.warning("f6_eval_error", ticker=ticker, error=str(e))
        return signals

    async def _evaluate(self, ticker: str, market_data: Any) -> StrategySignal | None:
        # Aggregate sentiment over rolling window
        news_sentiment = await market_data.get_finbert_rolling_sentiment(
            ticker, window_hours=ROLLING_WINDOW_HOURS
        )
        analyst_upgrade = await market_data.get_recent_analyst_upgrade(ticker)
        if analyst_upgrade:
            news_sentiment += ANALYST_UPGRADE_BONUS / 100

        unusual_options = await market_data.get_unusual_options_activity(ticker)
        vwap_position = await market_data.get_vwap_position(ticker)  # "ABOVE" | "BELOW"
        put_call_ratio = await market_data.get_put_call_ratio(ticker)

        if news_sentiment >= LONG_SENTIMENT_THRESHOLD and unusual_options and vwap_position == "ABOVE":
            direction = "LONG"
        elif (
            news_sentiment <= SHORT_SENTIMENT_THRESHOLD
            and put_call_ratio >= MIN_PUT_CALL_RATIO_SHORT
            and vwap_position == "BELOW"
        ):
            direction = "SHORT"
        else:
            return None

        price = await market_data.get_current_price(ticker)
        atr = await market_data.get_atr(ticker, period=14)
        entry = price
        sl = entry - atr if direction == "LONG" else entry + atr
        tp = entry + atr * 2 if direction == "LONG" else entry - atr * 2

        confidence = abs(news_sentiment)
        filters = ["FINBERT_SENTIMENT", "VWAP_CONFIRM"]
        if unusual_options:
            filters.append("UNUSUAL_OPTIONS")
        if analyst_upgrade:
            filters.append("ANALYST_UPGRADE")

        return StrategySignal(
            instrument=ticker,
            direction=direction,
            entry_price=entry,
            stop_loss=sl,
            take_profit=tp,
            lot_size=0.0,
            confidence_score=min(1.0, confidence),
            strategy=self.name,
            strategy_type=self.strategy_type,
            filters_passed=filters,
            notes=f"Sentiment={news_sentiment:.2f}, P/C ratio={put_call_ratio:.2f}",
        )
