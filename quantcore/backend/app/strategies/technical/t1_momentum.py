"""
T1 — Momentum Breakout (Stocks & Forex)
Captures strong directional moves after consolidation breaks.
"""
from __future__ import annotations
from typing import Any
import structlog
from app.strategies.base import BaseStrategy, StrategySignal

log = structlog.get_logger()

BB_SQUEEZE_THRESHOLD_PCT = 0.20
VOLUME_SPIKE_MULTIPLIER = 2.0
ADX_MIN = 25
ATR_SL_MULTIPLE = 1.5
ATR_TP_MULTIPLE = 3.0
PRE_NEWS_BLOCK_MINUTES = 30


class MomentumBreakoutStrategy(BaseStrategy):
    name = "MomentumBreakout"
    strategy_type = "TECHNICAL"

    async def scan(self, instruments: list[str], market_data: Any) -> list[StrategySignal]:
        signals: list[StrategySignal] = []
        for instrument in instruments:
            try:
                sig = await self._evaluate(instrument, market_data)
                if sig:
                    signals.append(sig)
            except Exception as e:
                log.warning("t1_eval_error", instrument=instrument, error=str(e))
        return signals

    async def _evaluate(self, instrument: str, market_data: Any) -> StrategySignal | None:
        # News calendar check — no entry 30 min pre-news
        mins_to_news = await market_data.minutes_to_next_news_event(instrument)
        if mins_to_news is not None and mins_to_news <= PRE_NEWS_BLOCK_MINUTES:
            return None

        # Bollinger Band squeeze
        bb = await market_data.get_bollinger_bands(instrument, period=20)
        bb_bandwidth = (bb["upper"] - bb["lower"]) / bb["middle"]
        avg_bandwidth = await market_data.get_avg_bb_bandwidth(instrument, lookback=20)
        if bb_bandwidth >= avg_bandwidth * BB_SQUEEZE_THRESHOLD_PCT + avg_bandwidth:
            return None  # not squeezed

        # Volume spike
        current_volume = await market_data.get_current_volume(instrument)
        avg_volume = await market_data.get_avg_volume(instrument, period=20)
        if current_volume < avg_volume * VOLUME_SPIKE_MULTIPLIER:
            return None

        # ADX trend strength
        adx = await market_data.get_adx(instrument, period=14)
        if adx < ADX_MIN:
            return None

        # RSI direction confirmation
        rsi = await market_data.get_rsi(instrument, period=14)
        price = await market_data.get_current_price(instrument)
        prev_resistance = await market_data.get_key_level(instrument, "resistance")
        prev_support = await market_data.get_key_level(instrument, "support")

        if price > prev_resistance and rsi > 50:
            direction = "LONG"
            level = prev_resistance
        elif price < prev_support and rsi < 50:
            direction = "SHORT"
            level = prev_support
        else:
            return None

        atr = await market_data.get_atr(instrument, period=14)
        entry = price
        sl = entry - atr * ATR_SL_MULTIPLE if direction == "LONG" else entry + atr * ATR_SL_MULTIPLE
        tp = entry + atr * ATR_TP_MULTIPLE if direction == "LONG" else entry - atr * ATR_TP_MULTIPLE
        rr = self._compute_rr_ratio(entry, sl, tp)

        if rr < 2.0:
            return None

        confidence = min(1.0, (adx / 50) * (current_volume / (avg_volume * 3)))

        return StrategySignal(
            instrument=instrument,
            direction=direction,
            entry_price=entry,
            stop_loss=sl,
            take_profit=tp,
            lot_size=0.0,
            confidence_score=confidence,
            strategy=self.name,
            strategy_type=self.strategy_type,
            filters_passed=["BB_SQUEEZE", "VOLUME_SPIKE", "ADX", "RSI", "NEWS_CALENDAR", "RR_RATIO"],
            notes=f"ADX={adx:.1f}, Vol×{current_volume/avg_volume:.1f}, RR={rr:.1f}",
        )
