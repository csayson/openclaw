"""
F5 — Insider Trading Signal Replication
Mirrors statistically significant open-market insider purchases from SEC Form 4.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
import structlog
from app.strategies.base import BaseStrategy, StrategySignal

log = structlog.get_logger()

MIN_PURCHASE_USD = 100_000
MIN_SIGNAL_SCORE = 50
HOLD_DAYS = (30, 90)
PROFIT_TARGET_PCT = 0.20


@dataclass
class InsiderFiling:
    ticker: str
    insider_title: str
    purchase_usd: float
    transaction_type: str  # "P" = open market purchase
    holdings_pct: float
    filed_at: datetime


class InsiderSignalStrategy(BaseStrategy):
    name = "InsiderSignal"
    strategy_type = "FUNDAMENTAL"

    async def scan(self, instruments: list[str], market_data: Any) -> list[StrategySignal]:
        signals: list[StrategySignal] = []
        filings = await market_data.get_form4_filings(since_hours=24)

        grouped: dict[str, list[InsiderFiling]] = {}
        for f in filings:
            if f.transaction_type != "P" or f.purchase_usd < MIN_PURCHASE_USD:
                continue
            grouped.setdefault(f.ticker, []).append(f)

        for ticker, ticker_filings in grouped.items():
            try:
                sig = await self._evaluate(ticker, ticker_filings, market_data)
                if sig:
                    signals.append(sig)
            except Exception as e:
                log.warning("f5_eval_error", ticker=ticker, error=str(e))
        return signals

    async def _evaluate(
        self, ticker: str, filings: list[InsiderFiling], market_data: Any
    ) -> StrategySignal | None:
        score = self._score(filings)
        if score < MIN_SIGNAL_SCORE:
            return None

        price = await market_data.get_current_price(ticker)
        atr = await market_data.get_atr(ticker, period=14)
        near_52w_low = await market_data.is_near_52w_low(ticker, threshold_pct=0.10)

        entry = price
        sl = entry - atr * 2
        tp = entry * (1 + PROFIT_TARGET_PCT)
        confidence = min(1.0, score / 100)

        filters = ["FORM4_OPEN_MARKET", f"SCORE_{score}"]
        if near_52w_low:
            filters.append("NEAR_52W_LOW")

        return StrategySignal(
            instrument=ticker,
            direction="LONG",
            entry_price=entry,
            stop_loss=sl,
            take_profit=tp,
            lot_size=0.0,
            confidence_score=confidence,
            fundamental_score=float(score),
            strategy=self.name,
            strategy_type=self.strategy_type,
            filters_passed=filters,
            notes=f"{len(filings)} insiders, total ${sum(f.purchase_usd for f in filings):,.0f}",
        )

    @staticmethod
    def _score(filings: list[InsiderFiling]) -> int:
        score = 0
        titles = {f.insider_title.upper() for f in filings}
        if any(t in titles for t in {"CEO", "CFO", "CHIEF EXECUTIVE", "CHIEF FINANCIAL"}):
            score += 30
        if len(filings) >= 3:
            score += 25
        if any(f.purchase_usd >= 500_000 for f in filings):
            score += 20
        # Cluster within 5 days
        if len(filings) >= 2:
            dates = sorted(f.filed_at for f in filings)
            if (dates[-1] - dates[0]).days <= 5:
                score += 10
        return score
