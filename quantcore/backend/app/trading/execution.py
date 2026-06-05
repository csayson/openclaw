"""
Execution pipeline — validates, scores, sizes, submits, monitors, and logs trades.
Steps: VALIDATE → SCORE → SIZE → SUBMIT → CHART → MONITOR → CLOSE → LOG → REPORT
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.trading.state_machine import TradingStateMachine
from app.trading.risk_manager import RiskManager
from app.models.trade import Trade, Signal, TradeStatus, TradeDirection, StrategyType

log = structlog.get_logger()

SLIPPAGE_GUARD_PIPS = 3
SLIPPAGE_GUARD_PCT = 0.0005


class ExecutionPipeline:
    def __init__(self, db: AsyncSession, redis: Any, risk_manager: RiskManager):
        self._db = db
        self._redis = redis
        self._risk = risk_manager

    async def process_signal(
        self,
        signal: dict,
        account_id: str,
        state_machine: TradingStateMachine,
        broker: Any,
        account_metrics: Any,
    ) -> Trade | None:
        # STEP 1: VALIDATE
        if not await state_machine.is_new_entry_allowed():
            log.debug("signal_dropped_state_not_active", signal_id=signal.get("signal_id"))
            return None

        risk_result = self._risk.check_new_trade(
            metrics=account_metrics,
            instrument=signal["instrument"],
            entry_price=signal["entry_price"],
            stop_loss=signal["stop_loss"],
            win_rate_estimate=signal.get("win_rate_estimate", 0.5),
            avg_win_loss_ratio=signal.get("risk_reward_ratio", 2.0),
        )
        if not risk_result.allowed:
            log.info("signal_rejected_risk", reason=risk_result.reason, signal_id=signal.get("signal_id"))
            return None

        # STEP 2: SCORE — confluence already embedded in confidence_score
        if signal.get("confidence_score", 0) < 0.6:
            log.debug("signal_rejected_low_confidence", score=signal.get("confidence_score"))
            return None

        # STEP 3: SIZE
        lot_size = min(risk_result.max_lot_size, signal.get("lot_size", risk_result.max_lot_size))

        # STEP 4: SUBMIT bracket order (entry + TP + SL OCO)
        broker_order_id = None
        try:
            broker_order_id = await broker.submit_bracket_order(
                instrument=signal["instrument"],
                direction=signal["direction"],
                lot_size=lot_size,
                entry_price=signal["entry_price"],
                stop_loss=signal["stop_loss"],
                take_profit=signal["take_profit"],
            )
        except Exception as e:
            log.error("order_submission_failed", error=str(e), signal=signal.get("signal_id"))
            return None

        # STEP 5: Create DB record
        trade = Trade(
            id=str(uuid.uuid4()),
            account_id=account_id,
            signal_id=signal.get("signal_id"),
            broker_order_id=broker_order_id,
            instrument=signal["instrument"],
            direction=TradeDirection(signal["direction"]),
            status=TradeStatus.OPEN,
            strategy_name=signal["strategy"],
            strategy_type=StrategyType(signal.get("strategy_type", "TECHNICAL")),
            market_regime=signal.get("regime"),
            entry_price=signal["entry_price"],
            stop_loss=signal["stop_loss"],
            take_profit=signal["take_profit"],
            lot_size=lot_size,
            risk_amount_usd=risk_result.risk_amount_usd,
            risk_reward_ratio=signal.get("risk_reward_ratio"),
            confidence_score=signal.get("confidence_score"),
            fundamental_score=signal.get("fundamental_score"),
            filters_passed=signal.get("filters_passed", []),
            opened_at=datetime.now(timezone.utc),
        )
        self._db.add(trade)
        await self._db.commit()
        await self._db.refresh(trade)

        # STEP 6: Notify chart engine to render this instrument
        await self._redis.publish(
            "qc:chart_events",
            f'{{"action":"RENDER","instrument":"{signal["instrument"]}","trade_id":"{trade.id}"}}',
        )

        # STEP 9+10: Queue for logging and reporting
        await self._redis.lpush("qc:report_queue", trade.id)

        log.info(
            "trade_opened",
            trade_id=trade.id,
            instrument=trade.instrument,
            direction=trade.direction,
            lot_size=lot_size,
            broker_order=broker_order_id,
        )
        return trade

    async def close_trade(self, trade_id: str, exit_price: float, exit_reason: str, broker: Any):
        trade = await self._db.get(Trade, trade_id)
        if not trade or trade.status != TradeStatus.OPEN:
            return

        direction_multiplier = 1 if trade.direction == TradeDirection.LONG else -1
        pnl = (exit_price - trade.entry_price) * direction_multiplier * trade.lot_size
        pnl_pct = pnl / (trade.entry_price * trade.lot_size) * 100 if trade.lot_size else 0

        trade.exit_price = exit_price
        trade.status = TradeStatus.CLOSED
        trade.pnl_usd = pnl
        trade.pnl_pct = pnl_pct
        trade.exit_reason = exit_reason
        trade.closed_at = datetime.now(timezone.utc)
        await self._db.commit()

        # STEP 8: Notify chart engine to collapse chart if no remaining positions
        await self._redis.publish(
            "qc:chart_events",
            f'{{"action":"CHECK_COLLAPSE","instrument":"{trade.instrument}"}}',
        )
        log.info("trade_closed", trade_id=trade_id, pnl_usd=pnl, exit_reason=exit_reason)
