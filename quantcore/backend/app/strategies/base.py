from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
import structlog

log = structlog.get_logger()


@dataclass
class StrategySignal:
    instrument: str
    direction: str  # "LONG" | "SHORT"
    entry_price: float
    stop_loss: float
    take_profit: float
    lot_size: float
    confidence_score: float
    strategy: str
    strategy_type: str  # "FUNDAMENTAL" | "TECHNICAL"
    filters_passed: list[str] = field(default_factory=list)
    fundamental_score: float | None = None
    regime: str | None = None
    notes: str = ""


class BaseStrategy(ABC):
    name: str = "BaseStrategy"
    strategy_type: str = "TECHNICAL"

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.log = log.bind(strategy=self.name)

    @abstractmethod
    async def scan(self, instruments: list[str], market_data: Any) -> list[StrategySignal]:
        """Scan instruments and return signals."""
        ...

    def _compute_rr_ratio(self, entry: float, stop: float, target: float) -> float:
        risk = abs(entry - stop)
        reward = abs(target - entry)
        return reward / risk if risk > 0 else 0.0
