"""
Abstract broker interface — all broker adapters implement this.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class OrderResult:
    broker_order_id: str
    status: str
    filled_price: float | None = None
    message: str = ""


class BaseBroker(ABC):
    name: str = "BaseBroker"

    @abstractmethod
    async def connect(self): ...

    @abstractmethod
    async def disconnect(self): ...

    @abstractmethod
    async def submit_bracket_order(
        self,
        instrument: str,
        direction: str,
        lot_size: float,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
    ) -> str:
        """Returns broker_order_id."""
        ...

    @abstractmethod
    async def cancel_pending_orders(self, account_id: str): ...

    @abstractmethod
    async def close_all_positions(self, account_id: str): ...

    @abstractmethod
    async def tighten_trailing_stops(self, account_id: str, factor: float = 0.80): ...

    @abstractmethod
    async def get_open_position_count(self, account_id: str) -> int: ...

    @abstractmethod
    async def get_account_equity(self, account_id: str) -> float: ...

    @abstractmethod
    async def get_open_positions(self, account_id: str) -> list[dict]: ...
