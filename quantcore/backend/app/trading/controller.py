"""
TradingController — orchestrates start/stop/pause/emergency across the state machine,
broker connections, and open position management.
"""
from __future__ import annotations
import asyncio
from datetime import datetime, timezone
from typing import TYPE_CHECKING
import structlog
from redis.asyncio import Redis

from app.trading.state_machine import TradingStateMachine, TradingState, StopMode
from app.core.config import settings

if TYPE_CHECKING:
    from app.brokers.base import BaseBroker

log = structlog.get_logger()


class TradingStatus:
    def __init__(
        self,
        state: TradingState,
        active_strategies: list[str],
        open_positions: int,
        started_at: datetime | None,
        account_id: str,
    ):
        self.state = state
        self.active_strategies = active_strategies
        self.open_positions = open_positions
        self.started_at = started_at
        self.account_id = account_id

    def dict(self) -> dict:
        return {
            "state": self.state.value,
            "active_strategies": self.active_strategies,
            "open_positions": self.open_positions,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "account_id": self.account_id,
        }


class TradingController:
    def __init__(self, redis: Redis):
        self._redis = redis
        self._state_machines: dict[str, TradingStateMachine] = {}
        self._active_strategies: dict[str, list[str]] = {}
        self._brokers: dict[str, "BaseBroker"] = {}
        self._wind_down_tasks: dict[str, asyncio.Task] = {}

    def _get_sm(self, account_id: str) -> TradingStateMachine:
        if account_id not in self._state_machines:
            self._state_machines[account_id] = TradingStateMachine(self._redis, account_id)
        return self._state_machines[account_id]

    async def connect(self, account_id: str, broker: "BaseBroker"):
        sm = self._get_sm(account_id)
        await broker.connect()
        self._brokers[account_id] = broker
        await sm.transition(TradingState.CONNECTED, triggered_by="connect")
        log.info("broker_connected", account=account_id, broker=broker.name)

    async def disconnect(self, account_id: str):
        sm = self._get_sm(account_id)
        broker = self._brokers.pop(account_id, None)
        if broker:
            await broker.disconnect()
        await sm.transition(TradingState.OFFLINE, triggered_by="disconnect")

    async def start(self, account_id: str, strategies: list[str], user: str = "user"):
        sm = self._get_sm(account_id)
        await sm.transition(TradingState.ACTIVE, triggered_by=user)
        self._active_strategies[account_id] = strategies
        await self._redis.hset(
            f"qc:active_strategies:{account_id}",
            mapping={s: "1" for s in strategies},
        )
        log.info("trading_started", account=account_id, strategies=strategies, user=user)

    async def stop(self, account_id: str, mode: StopMode, user: str = "user"):
        sm = self._get_sm(account_id)
        broker = self._brokers.get(account_id)

        if mode == StopMode.PAUSE:
            await sm.transition(TradingState.PAUSED, triggered_by=user)
            log.info("trading_paused", account=account_id)

        elif mode == StopMode.SOFT:
            await sm.transition(TradingState.WINDING_DOWN, triggered_by=user)
            # Cancel unfilled pending orders; leave open positions managed
            if broker:
                await broker.cancel_pending_orders(account_id)
            # Tighten trailing stops by 20% on all open positions
            if broker:
                await broker.tighten_trailing_stops(account_id, factor=0.80)
            # Monitor until all positions close, then → CONNECTED
            task = asyncio.create_task(self._wind_down_monitor(account_id))
            self._wind_down_tasks[account_id] = task
            log.info("soft_stop_activated", account=account_id)

        elif mode == StopMode.HARD:
            await sm.transition(TradingState.WINDING_DOWN, triggered_by=user)
            if broker:
                await broker.cancel_pending_orders(account_id)
                await broker.close_all_positions(account_id)
            await sm.transition(TradingState.CONNECTED, triggered_by="hard_stop_complete")
            log.info("hard_stop_complete", account=account_id)

    async def resume(self, account_id: str, user: str = "user"):
        sm = self._get_sm(account_id)
        await sm.transition(TradingState.ACTIVE, triggered_by=user)
        log.info("trading_resumed", account=account_id)

    async def emergency_stop(self, account_id: str, user: str = "user"):
        sm = self._get_sm(account_id)
        broker = self._brokers.get(account_id)
        # Cancel all orders and close all positions simultaneously
        tasks = []
        if broker:
            tasks.append(broker.cancel_pending_orders(account_id))
            tasks.append(broker.close_all_positions(account_id))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        await sm.transition(TradingState.EMERGENCY, triggered_by=user)
        # Disconnect broker
        if broker:
            await broker.disconnect()
            self._brokers.pop(account_id, None)
        await sm.transition(TradingState.OFFLINE, triggered_by="emergency_cleanup")
        # Fire notifications
        await self._send_emergency_alerts(account_id)
        log.critical("emergency_stop", account=account_id, user=user)

    async def get_status(self, account_id: str) -> TradingStatus:
        sm = self._get_sm(account_id)
        state = await sm.get_state()
        strategies = self._active_strategies.get(account_id, [])
        broker = self._brokers.get(account_id)
        open_count = 0
        if broker:
            try:
                open_count = await broker.get_open_position_count(account_id)
            except Exception:
                pass
        started_raw = await self._redis.get(f"qc:started_at:{account_id}")
        started_at = datetime.fromisoformat(started_raw) if started_raw else None
        return TradingStatus(
            state=state,
            active_strategies=strategies,
            open_positions=open_count,
            started_at=started_at,
            account_id=account_id,
        )

    async def _wind_down_monitor(self, account_id: str):
        broker = self._brokers.get(account_id)
        sm = self._get_sm(account_id)
        while True:
            await asyncio.sleep(10)
            if not broker:
                break
            try:
                count = await broker.get_open_position_count(account_id)
                if count == 0:
                    await sm.transition(TradingState.CONNECTED, triggered_by="wind_down_complete")
                    log.info("wind_down_complete", account=account_id)
                    break
            except Exception as e:
                log.error("wind_down_monitor_error", error=str(e))

    async def _send_emergency_alerts(self, account_id: str):
        # Notifications dispatched via Celery task to avoid blocking
        try:
            from app.tasks.notifications import send_emergency_alert_task
            send_emergency_alert_task.delay(account_id)
        except Exception as e:
            log.error("emergency_alert_dispatch_failed", error=str(e))
