from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Literal
import structlog

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.account import User, TradingAccount, BrokerConnection, AccountType

log = structlog.get_logger()
router = APIRouter(prefix="/accounts", tags=["accounts"])


class CreateAccountRequest(BaseModel):
    account_type: Literal["DEMO", "LIVE"]
    broker: str
    starting_capital: float = 10000.0
    risk_tolerance: float = 0.5
    max_daily_loss_pct: float = 3.0
    max_open_positions: int = 8
    enabled_markets: dict = {}
    enabled_strategies: dict = {}


class BrokerConnectRequest(BaseModel):
    broker_name: str
    api_key: str
    api_secret: str
    server_url: str | None = None
    is_demo: bool = True
    account_id: str


class AccountResponse(BaseModel):
    id: str
    account_type: str
    broker: str
    starting_capital: float
    current_equity: float
    trading_state: str
    risk_tolerance: float
    max_daily_loss_pct: float
    max_open_positions: int
    enabled_markets: dict
    kyc_status: str

    class Config:
        from_attributes = True


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=AccountResponse)
async def create_account(
    body: CreateAccountRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    account = TradingAccount(
        user_id=current_user.id,
        account_type=AccountType(body.account_type),
        broker=body.broker,
        starting_capital=body.starting_capital,
        current_equity=body.starting_capital,
        risk_tolerance=body.risk_tolerance,
        max_daily_loss_pct=body.max_daily_loss_pct,
        max_open_positions=body.max_open_positions,
        enabled_markets=body.enabled_markets,
        enabled_strategies=body.enabled_strategies,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


@router.get("/", response_model=list[AccountResponse])
async def list_accounts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TradingAccount).where(TradingAccount.user_id == current_user.id)
    )
    return result.scalars().all()


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    account = await db.get(TradingAccount, account_id)
    if not account or account.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.post("/brokers/connect")
async def connect_broker(
    body: BrokerConnectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    account = await db.get(TradingAccount, body.account_id)
    if not account or account.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Account not found")

    conn = BrokerConnection(
        account_id=body.account_id,
        broker_name=body.broker_name,
        server_url=body.server_url,
        is_demo=body.is_demo,
        is_connected=False,
    )
    db.add(conn)
    await db.commit()
    await db.refresh(conn)
    # TODO: Test actual broker connection here
    return {"connection_id": conn.id, "status": "created"}


@router.get("/{account_id}/brokers")
async def list_broker_connections(
    account_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    account = await db.get(TradingAccount, account_id)
    if not account or account.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Account not found")
    result = await db.execute(
        select(BrokerConnection).where(BrokerConnection.account_id == account_id)
    )
    conns = result.scalars().all()
    return [
        {
            "id": c.id,
            "broker_name": c.broker_name,
            "server_url": c.server_url,
            "is_demo": c.is_demo,
            "is_connected": c.is_connected,
            "last_connected_at": c.last_connected_at,
            "latency_ms": c.latency_ms,
        }
        for c in conns
    ]
