"""
T4 — High-Frequency Scalping (Forex 1m–5m)
Accumulates gains from micro price movements during London/NY overlap.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
import structlog
from app.strategies.base import BaseStrategy, StrategySignal

log = structlog.get_logger()

LONDON_NY_START_HOUR_EST = 8
LONDON_NY_END_HOUR_EST = 12
MAX_SPREAD_PIPS = 1.5
PIP_TARGET = 8
PIP_STOP = 5
MIN_RR = 1.2
MAX_DAILY_TRADES = 20
MAX_CONSECUTIVE_LOSSES = 3


class ScalpingStrategy(BaseStrategy):
    name = "HFScalping"
    strategy_type = "TECHNICAL"

    def __init__(self, config: dict | None = None):
        super().__init__(config)
        self._daily_trade_count: dict[str, int] = {}
        self._consecutive_losses: dict[str, int] = {}

    async def scan(self, instruments: list[str], market_data: Any) -> list[StrategySignal]:
        if not self._is_london_ny_overlap():
            return []

        signals: list[StrategySignal] = []
        for instrument in instruments:
            try:
                daily_count = self._daily_trade_count.get(instrument, 0)
                consec_loss = self._consecutive_losses.get(instrument, 0)
                if daily_count >= MAX_DAILY_TRADES or consec_loss >= MAX_CONSECUTIVE_LOSSES:
                    continue
                sig = await self._evaluate(instrument, market_data)
                if sig:
                    signals.append(sig)
            except Exception as e:
                log.warning("t4_eval_error", instrument=instrument, error=str(e))
        return signals

    async def _evaluate(self, instrument: str, market_data: Any) -> StrategySignal | None:
        spread_pips = await market_data.get_spread_pips(instrument)
        if spread_pips > MAX_SPREAD_PIPS:
            return None

        vwap_trend = await market_data.get_vwap_trend(instrument)
        ema8 = await market_data.get_ema(instrument, period=8, timeframe="1m")
        ema21 = await market_data.get_ema(instrument, period=21, timeframe="1m")
        price = await market_data.get_current_price(instrument)
        pip_size = await market_data.get_pip_size(instrument)

        if ema8 > ema21 and vwap_trend == "UP" and price > ema8:
            direction = "LONG"
        elif ema8 < ema21 and vwap_trend == "DOWN" and price < ema8:
            direction = "SHORT"
        else:
            return None

        entry = price
        sl = entry - PIP_STOP * pip_size if direction == "LONG" else entry + PIP_STOP * pip_size
        tp = entry + PIP_TARGET * pip_size if direction == "LONG" else entry - PIP_TARGET * pip_size
        rr = PIP_TARGET / PIP_STOP

        if rr < MIN_RR:
            return None

        return StrategySignal(
            instrument=instrument,
            direction=direction,
            entry_price=entry,
            stop_loss=sl,
            take_profit=tp,
            lot_size=0.0,
            confidence_score=0.70,
            strategy=self.name,
            strategy_type=self.strategy_type,
            filters_passed=["LONDON_NY_SESSION", "SPREAD", "EMA_CROSS", "VWAP"],
            notes=f"EMA8={ema8:.5f}, EMA21={ema21:.5f}, spread={spread_pips:.1f}pips",
        )

    @staticmethod
    def _is_london_ny_overlap() -> bool:
        now = datetime.now(timezone.utc)
        est_hour = (now.hour - 5) % 24  # rough EST offset
        return LONDON_NY_START_HOUR_EST <= est_hour < LONDON_NY_END_HOUR_EST
