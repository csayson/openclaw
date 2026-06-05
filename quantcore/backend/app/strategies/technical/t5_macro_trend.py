"""
T5 — Macro Trend Following (Swing/Position)
Rides multi-week trends driven by central bank policy divergence.
"""
from __future__ import annotations
from typing import Any
import structlog
from app.strategies.base import BaseStrategy, StrategySignal

log = structlog.get_logger()

RISK_PCT = 1.0


class MacroTrendStrategy(BaseStrategy):
    name = "MacroTrendFollow"
    strategy_type = "TECHNICAL"

    async def scan(self, instruments: list[str], market_data: Any) -> list[StrategySignal]:
        signals: list[StrategySignal] = []
        for instrument in instruments:
            try:
                sig = await self._evaluate(instrument, market_data)
                if sig:
                    signals.append(sig)
            except Exception as e:
                log.warning("t5_eval_error", instrument=instrument, error=str(e))
        return signals

    async def _evaluate(self, instrument: str, market_data: Any) -> StrategySignal | None:
        # Daily 200 EMA trend bias
        ema200_daily = await market_data.get_ema(instrument, period=200, timeframe="1D")
        price_daily = await market_data.get_current_price(instrument)
        trend_bias = "LONG" if price_daily > ema200_daily else "SHORT"

        # COT net positioning alignment
        cot_bias = await market_data.get_cot_bias(instrument)
        if cot_bias != trend_bias:
            return None

        # Rate differential favorable
        rate_diff_ok = await market_data.get_rate_differential_ok(instrument, direction=trend_bias)
        if not rate_diff_ok:
            return None

        # DXY conflict check for FX
        dxy_conflict = await market_data.check_dxy_conflict(instrument, direction=trend_bias)
        if dxy_conflict:
            return None

        # 4H pullback to 50 EMA + confirmation candle
        ema50_4h = await market_data.get_ema(instrument, period=50, timeframe="4H")
        price_4h = await market_data.get_current_price(instrument, timeframe="4H")
        near_50ema = abs(price_4h - ema50_4h) / ema50_4h < 0.003  # within 0.3%

        if not near_50ema:
            return None

        candle = await market_data.get_last_candle(instrument, timeframe="4H")
        is_bullish_engulf = candle.get("pattern") == "BULLISH_ENGULFING"
        is_bearish_engulf = candle.get("pattern") == "BEARISH_ENGULFING"

        if trend_bias == "LONG" and not is_bullish_engulf:
            return None
        if trend_bias == "SHORT" and not is_bearish_engulf:
            return None

        atr = await market_data.get_atr(instrument, period=14, timeframe="4H")
        entry = price_4h
        sl_buffer = atr * 0.5
        sl = entry - sl_buffer if trend_bias == "LONG" else entry + sl_buffer
        tp = entry + atr * 3 if trend_bias == "LONG" else entry - atr * 3

        return StrategySignal(
            instrument=instrument,
            direction=trend_bias,
            entry_price=entry,
            stop_loss=sl,
            take_profit=tp,
            lot_size=0.0,
            confidence_score=0.78,
            strategy=self.name,
            strategy_type=self.strategy_type,
            filters_passed=["EMA200_DAILY", "COT_ALIGN", "RATE_DIFF", "DXY_OK", "PULLBACK_50EMA", "ENGULF"],
            notes=f"200EMA={ema200_daily:.5f}, 50EMA_4H={ema50_4h:.5f}",
        )
