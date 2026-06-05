"""
T3 — Options Theta Decay (Income)
Harvests time decay by selling defined-risk options spreads.
"""
from __future__ import annotations
from typing import Any
import structlog
from app.strategies.base import BaseStrategy, StrategySignal

log = structlog.get_logger()

MIN_IVR = 50
SHORT_DELTA = 0.16
DTE_ENTRY_MIN = 30
DTE_ENTRY_MAX = 45
DTE_CLOSE_MIN = 21
PROFIT_CLOSE_PCT = 0.50
STOP_LOSS_MULTIPLIER = 2.0
MAX_BID_ASK_SPREAD = 0.10


class ThetaDecayStrategy(BaseStrategy):
    name = "ThetaDecay"
    strategy_type = "TECHNICAL"

    async def scan(self, instruments: list[str], market_data: Any) -> list[StrategySignal]:
        signals: list[StrategySignal] = []
        for instrument in instruments:
            try:
                sig = await self._evaluate(instrument, market_data)
                if sig:
                    signals.append(sig)
            except Exception as e:
                log.warning("t3_eval_error", instrument=instrument, error=str(e))
        return signals

    async def _evaluate(self, instrument: str, market_data: Any) -> StrategySignal | None:
        ivr = await market_data.get_ivr(instrument)
        if ivr < MIN_IVR:
            return None

        options_chain = await market_data.get_options_chain(instrument, dte_min=DTE_ENTRY_MIN, dte_max=DTE_ENTRY_MAX)
        if not options_chain:
            return None

        # Find short call and put strikes at ~16 delta
        short_call = self._find_strike_near_delta(options_chain["calls"], SHORT_DELTA)
        short_put = self._find_strike_near_delta(options_chain["puts"], -SHORT_DELTA)
        if not short_call or not short_put:
            return None

        # Check bid-ask spread
        if short_call.get("ask", 0) - short_call.get("bid", 0) > MAX_BID_ASK_SPREAD:
            return None
        if short_put.get("ask", 0) - short_put.get("bid", 0) > MAX_BID_ASK_SPREAD:
            return None

        # Check for binary events within DTE window
        binary_event = await market_data.has_binary_event_in_window(instrument, days=DTE_ENTRY_MAX)
        if binary_event:
            return None

        credit_received = short_call.get("bid", 0) + short_put.get("bid", 0)
        price = await market_data.get_current_price(instrument)

        return StrategySignal(
            instrument=instrument,
            direction="SHORT",  # Net short premium
            entry_price=price,
            stop_loss=credit_received * (1 + STOP_LOSS_MULTIPLIER),
            take_profit=credit_received * PROFIT_CLOSE_PCT,
            lot_size=1.0,  # 1 contract
            confidence_score=min(1.0, ivr / 100),
            strategy=self.name,
            strategy_type=self.strategy_type,
            filters_passed=["IVR", "DTE_WINDOW", "DELTA_16", "BID_ASK", "NO_BINARY_EVENT"],
            notes=f"IVR={ivr:.0f}, call_strike={short_call.get('strike')}, put_strike={short_put.get('strike')}, credit=${credit_received:.2f}",
        )

    @staticmethod
    def _find_strike_near_delta(chain: list[dict], target_delta: float) -> dict | None:
        return min(
            chain,
            key=lambda x: abs(x.get("delta", 9999) - target_delta),
            default=None,
        )
