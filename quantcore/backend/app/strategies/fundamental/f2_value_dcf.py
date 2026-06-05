"""
F2 — Value / DCF Mean Reversion
Buys fundamentally undervalued stocks at deep discount to intrinsic value.
"""
from __future__ import annotations
from typing import Any
import structlog
from app.strategies.base import BaseStrategy, StrategySignal

log = structlog.get_logger()

MARGIN_OF_SAFETY = 0.30
MIN_FUNDAMENTAL_SCORE = 65
TRANCHE_COUNT = 3


class FundamentalScorer:
    @staticmethod
    def score(metrics: dict) -> tuple[int, list[str]]:
        score = 0
        passed = []
        if metrics.get("revenue_growth_yoy", 0) > 0.10:
            score += 20; passed.append("REVENUE_GROWTH")
        if metrics.get("gross_margin_expanding", False):
            score += 20; passed.append("MARGIN_EXPANSION")
        if metrics.get("debt_equity", 9999) < 0.5:
            score += 15; passed.append("LOW_DEBT")
        if metrics.get("fcf_yield", 0) > 0.05:
            score += 20; passed.append("FCF_YIELD")
        if metrics.get("roe", 0) > 0.15:
            score += 15; passed.append("ROE")
        if metrics.get("insider_buying", False):
            score += 10; passed.append("INSIDER_BUYING")
        return score, passed


class ValueDCFStrategy(BaseStrategy):
    name = "FundamentalValue"
    strategy_type = "FUNDAMENTAL"

    async def scan(self, instruments: list[str], market_data: Any) -> list[StrategySignal]:
        signals: list[StrategySignal] = []
        for ticker in instruments:
            try:
                sig = await self._evaluate(ticker, market_data)
                if sig:
                    signals.append(sig)
            except Exception as e:
                log.warning("f2_eval_error", ticker=ticker, error=str(e))
        return signals

    async def _evaluate(self, ticker: str, market_data: Any) -> StrategySignal | None:
        metrics = await market_data.get_fundamentals(ticker)
        dcf = await self._compute_dcf(ticker, market_data)
        if dcf is None:
            return None

        price = await market_data.get_current_price(ticker)
        discount_pct = (dcf - price) / dcf
        if discount_pct < MARGIN_OF_SAFETY:
            return None

        # Valuation multiples filter
        if metrics.get("pe_ratio", 9999) >= metrics.get("sector_median_pe", 25):
            return None
        if metrics.get("pb_ratio", 9999) >= 1.5:
            return None
        if metrics.get("ev_ebitda", 9999) >= 10:
            return None

        # Technical entry trigger
        near_support = await market_data.is_near_52w_support(ticker)
        rsi = await market_data.get_rsi(ticker, period=14)
        if not near_support or rsi >= 35:
            return None

        fund_score, passed_filters = FundamentalScorer.score(metrics)
        if fund_score < MIN_FUNDAMENTAL_SCORE:
            return None

        atr = await market_data.get_atr(ticker, period=14)
        entry = price
        sl = entry * 0.85  # -15% from entry as specified
        tp = dcf  # target: DCF midpoint

        confidence = fund_score / 100 * (1 - rsi / 100)

        return StrategySignal(
            instrument=ticker,
            direction="LONG",
            entry_price=entry,
            stop_loss=sl,
            take_profit=tp,
            lot_size=0.0,
            confidence_score=confidence,
            fundamental_score=float(fund_score),
            strategy=self.name,
            strategy_type=self.strategy_type,
            filters_passed=passed_filters + ["DCF_DISCOUNT", "NEAR_SUPPORT", "RSI_OVERSOLD"],
            notes=f"DCF={dcf:.2f}, discount={discount_pct*100:.1f}%, score={fund_score}",
        )

    async def _compute_dcf(self, ticker: str, market_data: Any) -> float | None:
        try:
            fcf_history = await market_data.get_fcf_history(ticker, years=5)
            if not fcf_history or len(fcf_history) < 2:
                return None
            avg_fcf = sum(fcf_history) / len(fcf_history)
            growth_rate = 0.05  # conservative 5% terminal growth
            risk_free = await market_data.get_risk_free_rate()  # FRED API
            wacc = risk_free + 0.06  # + equity risk premium
            # Simple Gordon growth model for terminal value
            shares = await market_data.get_shares_outstanding(ticker)
            if shares == 0:
                return None
            intrinsic = (avg_fcf * (1 + growth_rate)) / (wacc - growth_rate)
            return intrinsic / shares
        except Exception:
            return None
