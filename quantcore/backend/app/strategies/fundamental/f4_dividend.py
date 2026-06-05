"""
F4 — Dividend Capture & Income
Systematic dividend capture with optional covered call overlay.
"""
from __future__ import annotations
from typing import Any
import structlog
from app.strategies.base import BaseStrategy, StrategySignal

log = structlog.get_logger()

MIN_YIELD = 0.03
MAX_PAYOUT_RATIO = 0.70
MIN_DIV_GROWTH_YEARS = 5
ENTRY_DAYS_BEFORE_EX = 7
MIN_CURRENT_RATIO = 1.5
MIN_EARNINGS_COVERAGE = 2.0


class DividendCaptureStrategy(BaseStrategy):
    name = "DividendCapture"
    strategy_type = "FUNDAMENTAL"

    async def scan(self, instruments: list[str], market_data: Any) -> list[StrategySignal]:
        signals: list[StrategySignal] = []
        upcoming_ex_dates = await market_data.get_upcoming_ex_dividend_dates(
            instruments, days_ahead=ENTRY_DAYS_BEFORE_EX + 2
        )
        for ticker, ex_date in upcoming_ex_dates.items():
            try:
                sig = await self._evaluate(ticker, ex_date, market_data)
                if sig:
                    signals.append(sig)
            except Exception as e:
                log.warning("f4_eval_error", ticker=ticker, error=str(e))
        return signals

    async def _evaluate(self, ticker: str, ex_date: Any, market_data: Any) -> StrategySignal | None:
        metrics = await market_data.get_fundamentals(ticker)

        # Quality filters
        if metrics.get("dividend_yield", 0) < MIN_YIELD:
            return None
        if metrics.get("payout_ratio", 1) > MAX_PAYOUT_RATIO:
            return None
        if metrics.get("div_growth_years", 0) < MIN_DIV_GROWTH_YEARS:
            return None
        if metrics.get("current_ratio", 0) < MIN_CURRENT_RATIO:
            return None
        if metrics.get("earnings_coverage", 0) < MIN_EARNINGS_COVERAGE:
            return None

        # Don't enter within 2 weeks of earnings
        days_to_earnings = await market_data.days_to_next_earnings(ticker)
        if days_to_earnings is not None and days_to_earnings < 14:
            return None

        price = await market_data.get_current_price(ticker)
        near_support = await market_data.is_near_support(ticker, window=20)
        if not near_support:
            return None

        dividend_per_share = metrics.get("dividend_per_share", 0)
        tp = price + dividend_per_share * 1.1  # recover dividend + slight premium
        sl = price * 0.97

        confidence = min(1.0, metrics.get("dividend_yield", 0) / 0.08)

        return StrategySignal(
            instrument=ticker,
            direction="LONG",
            entry_price=price,
            stop_loss=sl,
            take_profit=tp,
            lot_size=0.0,
            confidence_score=confidence,
            strategy=self.name,
            strategy_type=self.strategy_type,
            filters_passed=["DIV_YIELD", "PAYOUT_RATIO", "DIV_GROWTH", "CURRENT_RATIO", "NEAR_SUPPORT"],
            notes=f"Ex-date {ex_date}, yield={metrics.get('dividend_yield',0)*100:.1f}%",
        )
