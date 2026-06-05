"""
Redis-backed trading state machine.
State persists across restarts. All transitions are logged with timestamps.
"""
from __future__ import annotations
import asyncio
import enum
import json
from datetime import datetime, timezone
from typing import Callable
import structlog
from redis.asyncio import Redis

log = structlog.get_logger()

_STATE_KEY = "qc:state:{account_id}"
_HISTORY_KEY = "qc:state_history:{account_id}"


class TradingState(str, enum.Enum):
    OFFLINE = "OFFLINE"
    CONNECTED = "CONNECTED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    WINDING_DOWN = "WINDING_DOWN"
    EMERGENCY = "EMERGENCY"


class StopMode(str, enum.Enum):
    SOFT = "SOFT"
    HARD = "HARD"
    PAUSE = "PAUSE"


VALID_TRANSITIONS: dict[TradingState, set[TradingState]] = {
    TradingState.OFFLINE: {TradingState.CONNECTED},
    TradingState.CONNECTED: {TradingState.ACTIVE, TradingState.OFFLINE},
    TradingState.ACTIVE: {TradingState.PAUSED, TradingState.WINDING_DOWN, TradingState.CONNECTED, TradingState.EMERGENCY},
    TradingState.PAUSED: {TradingState.ACTIVE, TradingState.WINDING_DOWN, TradingState.EMERGENCY},
    TradingState.WINDING_DOWN: {TradingState.CONNECTED, TradingState.EMERGENCY},
    TradingState.EMERGENCY: {TradingState.OFFLINE},
}


class TradingStateMachine:
    def __init__(self, redis: Redis, account_id: str):
        self._redis = redis
        self._account_id = account_id
        self._state_key = _STATE_KEY.format(account_id=account_id)
        self._history_key = _HISTORY_KEY.format(account_id=account_id)
        self._listeners: list[Callable] = []

    async def get_state(self) -> TradingState:
        raw = await self._redis.get(self._state_key)
        if raw is None:
            await self._set_state(TradingState.OFFLINE, "init")
            return TradingState.OFFLINE
        return TradingState(raw)

    async def transition(self, target: TradingState, triggered_by: str = "system") -> TradingState:
        current = await self.get_state()
        if target not in VALID_TRANSITIONS.get(current, set()):
            raise ValueError(f"Invalid transition: {current} → {target}")
        await self._set_state(target, triggered_by)
        log.info("state_transition", account=self._account_id, from_=current, to=target, by=triggered_by)
        for listener in self._listeners:
            asyncio.create_task(listener(current, target))
        return target

    async def _set_state(self, state: TradingState, triggered_by: str):
        pipe = self._redis.pipeline()
        pipe.set(self._state_key, state.value)
        entry = json.dumps({
            "state": state.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "triggered_by": triggered_by,
        })
        pipe.lpush(self._history_key, entry)
        pipe.ltrim(self._history_key, 0, 499)  # keep last 500 transitions
        await pipe.execute()

    async def get_history(self, limit: int = 20) -> list[dict]:
        raw = await self._redis.lrange(self._history_key, 0, limit - 1)
        return [json.loads(r) for r in raw]

    def add_listener(self, fn: Callable):
        self._listeners.append(fn)

    async def is_new_entry_allowed(self) -> bool:
        state = await self.get_state()
        return state == TradingState.ACTIVE
