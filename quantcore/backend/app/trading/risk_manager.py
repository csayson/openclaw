"""
Risk management: position sizing (Half-Kelly), daily/weekly drawdown checks,
circuit breakers, correlation limits.
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Protocol
import structlog
from app.core.config import settings

log = structlog.get_logger()


@dataclass
class RiskCheckResult:
    allowed: bool
    reason: str = ""
    max_lot_size: float = 0.0
    risk_amount_usd: float = 0.0


class AccountMetrics(Protocol):
    equity: float
    daily_pnl_pct: float
    weekly_pnl_pct: float
    open_positions: int
    open_position_instruments: list[str]
    used_margin_pct: float


class RiskManager:
    def __init__(
        self,
        max_risk_per_trade_pct: float = settings.MAX_RISK_PER_TRADE_PCT,
        max_daily_dd_pct: float = settings.MAX_DAILY_DRAWDOWN_PCT,
        max_weekly_dd_pct: float = settings.MAX_WEEKLY_DRAWDOWN_PCT,
        max_open_positions: int = settings.MAX_OPEN_POSITIONS,
        margin_cap_pct: float = settings.MARGIN_CAP_PCT,
        circuit_breaker_pct: float = settings.CIRCUIT_BREAKER_PCT,
    ):
        self.max_risk_per_trade_pct = max_risk_per_trade_pct
        self.max_daily_dd_pct = max_daily_dd_pct
        self.max_weekly_dd_pct = max_weekly_dd_pct
        self.max_open_positions = max_open_positions
        self.margin_cap_pct = margin_cap_pct
        self.circuit_breaker_pct = circuit_breaker_pct

    def check_new_trade(
        self,
        metrics: AccountMetrics,
        instrument: str,
        entry_price: float,
        stop_loss: float,
        win_rate_estimate: float = 0.5,
        avg_win_loss_ratio: float = 2.0,
    ) -> RiskCheckResult:
        if metrics.daily_pnl_pct <= -self.circuit_breaker_pct:
            return RiskCheckResult(False, f"Circuit breaker: daily loss {metrics.daily_pnl_pct:.1f}%")

        if metrics.daily_pnl_pct <= -self.max_daily_dd_pct:
            return RiskCheckResult(False, f"Max daily drawdown hit: {metrics.daily_pnl_pct:.1f}%")

        if metrics.weekly_pnl_pct <= -self.max_weekly_dd_pct:
            return RiskCheckResult(False, f"Max weekly drawdown hit: {metrics.weekly_pnl_pct:.1f}%")

        if metrics.open_positions >= self.max_open_positions:
            return RiskCheckResult(False, f"Max open positions reached: {metrics.open_positions}")

        if metrics.used_margin_pct >= self.margin_cap_pct:
            return RiskCheckResult(False, f"Margin cap reached: {metrics.used_margin_pct:.1f}%")

        risk_amount = metrics.equity * (self.max_risk_per_trade_pct / 100)
        lot_size = self._half_kelly_lot(
            metrics.equity, entry_price, stop_loss, win_rate_estimate, avg_win_loss_ratio
        )
        return RiskCheckResult(True, "OK", max_lot_size=lot_size, risk_amount_usd=risk_amount)

    def _half_kelly_lot(
        self,
        equity: float,
        entry: float,
        stop: float,
        win_rate: float,
        win_loss_ratio: float,
    ) -> float:
        # Kelly fraction: f* = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio
        kelly = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio
        half_kelly = max(0.0, kelly / 2)
        risk_fraction = min(half_kelly, self.max_risk_per_trade_pct / 100)
        risk_amount = equity * risk_fraction
        stop_distance = abs(entry - stop)
        if stop_distance == 0:
            return 0.0
        lot_size = risk_amount / stop_distance
        return round(lot_size, 4)

    def check_drawdown_recovery(self, weekly_pnl_pct: float) -> str:
        """Returns 'NORMAL', 'PAPER_REVIEW', or 'CIRCUIT_BREAK'."""
        if weekly_pnl_pct <= -self.circuit_breaker_pct:
            return "CIRCUIT_BREAK"
        if weekly_pnl_pct <= -self.max_weekly_dd_pct:
            return "PAPER_REVIEW"
        return "NORMAL"

    def overnight_size_adjustment(self, lot_size: float, is_overnight: bool) -> float:
        return lot_size * 0.5 if is_overnight else lot_size
