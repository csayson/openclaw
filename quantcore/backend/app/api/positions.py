from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from datetime import datetime, date
import structlog

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.account import User
from app.models.trade import Trade, TradeStatus

log = structlog.get_logger()
router = APIRouter(prefix="/positions", tags=["positions"])


class TradeResponse(BaseModel):
    id: str
    instrument: str
    direction: str
    strategy_name: str
    entry_price: float | None
    current_price: float | None = None
    stop_loss: float | None
    take_profit: float | None
    lot_size: float
    pnl_usd: float | None
    pnl_pct: float | None
    status: str
    opened_at: datetime | None
    closed_at: datetime | None

    class Config:
        from_attributes = True


@router.get("/open", response_model=list[TradeResponse])
async def get_open_positions(
    account_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Trade).where(
            and_(Trade.account_id == account_id, Trade.status == TradeStatus.OPEN)
        ).order_by(desc(Trade.opened_at))
    )
    return result.scalars().all()


@router.get("/closed", response_model=list[TradeResponse])
async def get_closed_positions(
    account_id: str,
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    strategy: str | None = Query(None),
    limit: int = Query(100, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    filters = [Trade.account_id == account_id, Trade.status == TradeStatus.CLOSED]
    if from_date:
        filters.append(Trade.closed_at >= datetime.combine(from_date, datetime.min.time()))
    if to_date:
        filters.append(Trade.closed_at <= datetime.combine(to_date, datetime.max.time()))
    if strategy:
        filters.append(Trade.strategy_name == strategy)

    result = await db.execute(
        select(Trade).where(and_(*filters)).order_by(desc(Trade.closed_at)).limit(limit)
    )
    return result.scalars().all()


@router.get("/history/summary")
async def get_history_summary(
    account_id: str,
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    filters = [Trade.account_id == account_id, Trade.status == TradeStatus.CLOSED]
    if from_date:
        filters.append(Trade.closed_at >= datetime.combine(from_date, datetime.min.time()))
    if to_date:
        filters.append(Trade.closed_at <= datetime.combine(to_date, datetime.max.time()))

    result = await db.execute(select(Trade).where(and_(*filters)))
    trades = result.scalars().all()

    if not trades:
        return {"total_trades": 0, "net_pnl": 0.0, "win_rate": 0.0}

    wins = [t for t in trades if (t.pnl_usd or 0) > 0]
    net_pnl = sum(t.pnl_usd or 0 for t in trades)
    total_fees = sum(t.commission or 0 for t in trades)
    gross_pnl = net_pnl + total_fees
    pnls = [t.pnl_usd for t in trades if t.pnl_usd is not None]
    avg_win = sum(p for p in pnls if p > 0) / max(len([p for p in pnls if p > 0]), 1)
    avg_loss = sum(p for p in pnls if p < 0) / max(len([p for p in pnls if p < 0]), 1)

    return {
        "total_trades": len(trades),
        "wins": len(wins),
        "losses": len(trades) - len(wins),
        "win_rate": len(wins) / len(trades),
        "net_pnl": net_pnl,
        "gross_pnl": gross_pnl,
        "total_fees": total_fees,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "profit_factor": abs(avg_win / avg_loss) if avg_loss != 0 else 0,
        "largest_win": max((t.pnl_usd or 0 for t in trades), default=0),
        "largest_loss": min((t.pnl_usd or 0 for t in trades), default=0),
    }
