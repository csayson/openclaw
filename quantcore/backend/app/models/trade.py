from sqlalchemy import String, Float, Boolean, DateTime, Enum, JSON, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum
import uuid


class TradeDirection(str, enum.Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class TradeStatus(str, enum.Enum):
    PENDING = "PENDING"
    OPEN = "OPEN"
    CLOSING = "CLOSING"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class StrategyType(str, enum.Enum):
    FUNDAMENTAL = "FUNDAMENTAL"
    TECHNICAL = "TECHNICAL"


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("trading_accounts.id"), nullable=False)
    signal_id: Mapped[str | None] = mapped_column(String(50))
    broker_order_id: Mapped[str | None] = mapped_column(String(100))

    instrument: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    direction: Mapped[TradeDirection] = mapped_column(Enum(TradeDirection))
    status: Mapped[TradeStatus] = mapped_column(Enum(TradeStatus), default=TradeStatus.PENDING, index=True)
    strategy_name: Mapped[str] = mapped_column(String(50))
    strategy_type: Mapped[StrategyType] = mapped_column(Enum(StrategyType))
    market_regime: Mapped[str | None] = mapped_column(String(30))

    entry_price: Mapped[float | None] = mapped_column(Float)
    exit_price: Mapped[float | None] = mapped_column(Float)
    stop_loss: Mapped[float | None] = mapped_column(Float)
    take_profit: Mapped[float | None] = mapped_column(Float)
    lot_size: Mapped[float] = mapped_column(Float, default=0.0)
    risk_amount_usd: Mapped[float | None] = mapped_column(Float)
    risk_reward_ratio: Mapped[float | None] = mapped_column(Float)
    confidence_score: Mapped[float | None] = mapped_column(Float)
    fundamental_score: Mapped[float | None] = mapped_column(Float)

    pnl_usd: Mapped[float | None] = mapped_column(Float)
    pnl_pct: Mapped[float | None] = mapped_column(Float)
    commission: Mapped[float] = mapped_column(Float, default=0.0)
    slippage_pips: Mapped[float | None] = mapped_column(Float)

    filters_passed: Mapped[list] = mapped_column(JSON, default=list)
    entry_reason: Mapped[str | None] = mapped_column(Text)
    exit_reason: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    indicators_at_entry: Mapped[dict] = mapped_column(JSON, default=dict)

    opened_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("trading_accounts.id"))
    instrument: Mapped[str] = mapped_column(String(20), nullable=False)
    strategy: Mapped[str] = mapped_column(String(50))
    strategy_type: Mapped[str] = mapped_column(String(20))
    direction: Mapped[str] = mapped_column(String(5))
    entry_price: Mapped[float] = mapped_column(Float)
    stop_loss: Mapped[float] = mapped_column(Float)
    take_profit: Mapped[float] = mapped_column(Float)
    lot_size: Mapped[float] = mapped_column(Float)
    risk_amount_usd: Mapped[float] = mapped_column(Float)
    risk_reward_ratio: Mapped[float] = mapped_column(Float)
    confidence_score: Mapped[float] = mapped_column(Float)
    fundamental_score: Mapped[float | None] = mapped_column(Float)
    filters_passed: Mapped[list] = mapped_column(JSON, default=list)
    trading_state: Mapped[str] = mapped_column(String(20))
    new_entry_allowed: Mapped[bool] = mapped_column(Boolean)
    regime: Mapped[str | None] = mapped_column(String(30))
    session: Mapped[str | None] = mapped_column(String(30))
    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
