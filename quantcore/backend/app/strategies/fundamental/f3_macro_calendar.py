"""
F3 — Macro Economic Calendar Trading
Positions around high-impact macro data releases (NFP, CPI, FOMC, GDP, PMI).
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import structlog
from app.strategies.base import BaseStrategy, StrategySignal

log = structlog.get_logger()

TIER1_EVENTS = {"NFP", "CPI", "FOMC", "GDP", "PMI", "RETAIL_SALES", "PPI", "JOBLESS_CLAIMS"}
PRE_EVENT_RISK_PCT = 0.5
POST_EVENT_RISK_PCT = 1.0
DIVERGENCE_THRESHOLD_SIGMA = 1.0

CURRENCY_IMPACT_MATRIX = {
    "NFP_BEAT":    {"pair": "USDJPY", "direction": "LONG"},
    "CPI_ABOVE":   {"pair": "EURUSD", "direction": "SHORT"},
    "FOMC_HAWK":   {"pair": "USDX",   "direction": "LONG"},
    "GDP_MISS":    {"pair": "USDCAD", "direction": "SHORT"},
    "PMI_EXP":     {"pair": "GBPUSD", "direction": "LONG"},
}


@dataclass
class MacroEvent:
    name: str
    scheduled_at: Any
    consensus_forecast: float
    std_deviation: float


class MacroCalendarStrategy(BaseStrategy):
    name = "MacroCalendar"
    strategy_type = "FUNDAMENTAL"

    async def scan(self, instruments: list[str], market_data: Any) -> list[StrategySignal]:
        signals: list[StrategySignal] = []
        events = await market_data.get_upcoming_events(days_ahead=2, tier=1)

        for event in events:
            if event.name not in TIER1_EVENTS:
                continue
            try:
                pre_sig = await self._pre_event_signal(event, market_data)
                if pre_sig:
                    signals.append(pre_sig)
                post_sig = await self._post_event_reaction(event, market_data)
                if post_sig:
                    signals.append(post_sig)
            except Exception as e:
                log.warning("f3_eval_error", event=event.name, error=str(e))
        return signals

    async def _pre_event_signal(self, event: MacroEvent, market_data: Any) -> StrategySignal | None:
        model_forecast = await market_data.get_fred_model_forecast(event.name)
        divergence_sigma = (model_forecast - event.consensus_forecast) / (event.std_deviation or 1)
        if abs(divergence_sigma) < DIVERGENCE_THRESHOLD_SIGMA:
            return None

        impact_key = f"{event.name}_{'ABOVE' if divergence_sigma > 0 else 'BELOW'}"
        impact = CURRENCY_IMPACT_MATRIX.get(impact_key) or CURRENCY_IMPACT_MATRIX.get(
            f"{event.name}_{'BEAT' if divergence_sigma > 0 else 'MISS'}"
        )
        if not impact:
            return None

        price = await market_data.get_current_price(impact["pair"])
        atr = await market_data.get_atr(impact["pair"], period=14)
        direction = impact["direction"]
        entry = price
        sl = entry - atr if direction == "LONG" else entry + atr
        tp = entry + atr * 2 if direction == "LONG" else entry - atr * 2

        return StrategySignal(
            instrument=impact["pair"],
            direction=direction,
            entry_price=entry,
            stop_loss=sl,
            take_profit=tp,
            lot_size=0.0,
            confidence_score=min(1.0, abs(divergence_sigma) / 3),
            strategy=self.name,
            strategy_type=self.strategy_type,
            filters_passed=["TIER1_EVENT", "DIVERGENCE_THRESHOLD"],
            notes=f"Pre-event {event.name}, divergence={divergence_sigma:.2f}σ",
        )

    async def _post_event_reaction(self, event: MacroEvent, market_data: Any) -> StrategySignal | None:
        actual = await market_data.get_event_actual(event.name)
        if actual is None:
            return None  # event not yet released
        surprise = actual - event.consensus_forecast
        direction_str = "BEAT" if surprise > 0 else "MISS"
        impact_key = f"{event.name}_{direction_str}"
        impact = CURRENCY_IMPACT_MATRIX.get(impact_key)
        if not impact:
            return None

        price = await market_data.get_current_price(impact["pair"])
        atr = await market_data.get_atr(impact["pair"], period=14)
        direction = impact["direction"]
        entry = price
        sl = entry - atr * 0.75 if direction == "LONG" else entry + atr * 0.75
        tp = entry + atr * 1.5 if direction == "LONG" else entry - atr * 1.5

        return StrategySignal(
            instrument=impact["pair"],
            direction=direction,
            entry_price=entry,
            stop_loss=sl,
            take_profit=tp,
            lot_size=0.0,
            confidence_score=0.80,
            strategy=self.name,
            strategy_type=self.strategy_type,
            filters_passed=["TIER1_EVENT", "POST_RELEASE_CONFIRM"],
            notes=f"Post-event {event.name}, actual={actual}, surprise={surprise:+.2f}",
        )
