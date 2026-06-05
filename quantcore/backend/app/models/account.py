from sqlalchemy import String, Float, Boolean, DateTime, Enum, JSON, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum
import uuid


class AccountType(str, enum.Enum):
    DEMO = "DEMO"
    LIVE = "LIVE"


class KYCStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str | None] = mapped_column(String(30))
    country: Mapped[str | None] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    totp_secret: Mapped[str | None] = mapped_column(String(64))
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    lockout_until: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    accounts: Mapped[list["TradingAccount"]] = relationship("TradingAccount", back_populates="user")


class TradingAccount(Base):
    __tablename__ = "trading_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    account_type: Mapped[AccountType] = mapped_column(Enum(AccountType), default=AccountType.DEMO)
    broker: Mapped[str] = mapped_column(String(50))
    broker_account_id: Mapped[str | None] = mapped_column(String(100))
    kyc_status: Mapped[KYCStatus] = mapped_column(Enum(KYCStatus), default=KYCStatus.PENDING)
    starting_capital: Mapped[float] = mapped_column(Float, default=10000.0)
    current_equity: Mapped[float] = mapped_column(Float, default=10000.0)
    risk_tolerance: Mapped[float] = mapped_column(Float, default=0.5)  # 0=conservative, 1=aggressive
    max_daily_loss_pct: Mapped[float] = mapped_column(Float, default=3.0)
    max_open_positions: Mapped[int] = mapped_column(Integer, default=8)
    enabled_markets: Mapped[dict] = mapped_column(JSON, default=lambda: {"forex": True, "stocks": True, "options": False, "crypto": False})
    enabled_strategies: Mapped[dict] = mapped_column(JSON, default=lambda: {})
    trading_state: Mapped[str] = mapped_column(String(20), default="IDLE")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="accounts")
    broker_connections: Mapped[list["BrokerConnection"]] = relationship(
        "BrokerConnection", back_populates="account"
    )


class BrokerConnection(Base):
    __tablename__ = "broker_connections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("trading_accounts.id"), nullable=False)
    broker_name: Mapped[str] = mapped_column(String(50))
    server_url: Mapped[str | None] = mapped_column(String(255))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)
    is_connected: Mapped[bool] = mapped_column(Boolean, default=False)
    last_connected_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    latency_ms: Mapped[float | None] = mapped_column(Float)
    connection_meta: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    account: Mapped["TradingAccount"] = relationship("TradingAccount", back_populates="broker_connections")
