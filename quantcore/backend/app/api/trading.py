from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.database import get_db, get_redis
from app.api.auth import get_current_user
from app.models.account import User
from app.trading.controller import TradingController
from app.trading.state_machine import StopMode

log = structlog.get_logger()
router = APIRouter(prefix="/trading", tags=["trading"])

_controller: TradingController | None = None


def get_controller(redis=Depends(get_redis)) -> TradingController:
    global _controller
    if _controller is None:
        _controller = TradingController(redis)
    return _controller


class StartRequest(BaseModel):
    account_id: str
    strategies: list[str]


class StopRequest(BaseModel):
    account_id: str
    mode: StopMode = StopMode.SOFT


class EmergencyRequest(BaseModel):
    account_id: str
    confirm: str  # must be "CONFIRM"


@router.post("/start")
async def start_trading(
    body: StartRequest,
    current_user: User = Depends(get_current_user),
    controller: TradingController = Depends(get_controller),
):
    await controller.start(body.account_id, body.strategies, user=current_user.email)
    return {"status": "started", "strategies": body.strategies}


@router.post("/stop")
async def stop_trading(
    body: StopRequest,
    current_user: User = Depends(get_current_user),
    controller: TradingController = Depends(get_controller),
):
    await controller.stop(body.account_id, body.mode, user=current_user.email)
    return {"status": "stopped", "mode": body.mode}


@router.post("/pause")
async def pause_trading(
    account_id: str,
    current_user: User = Depends(get_current_user),
    controller: TradingController = Depends(get_controller),
):
    await controller.stop(account_id, StopMode.PAUSE, user=current_user.email)
    return {"status": "paused"}


@router.post("/resume")
async def resume_trading(
    account_id: str,
    current_user: User = Depends(get_current_user),
    controller: TradingController = Depends(get_controller),
):
    await controller.resume(account_id, user=current_user.email)
    return {"status": "resumed"}


@router.post("/emergency-stop")
async def emergency_stop(
    body: EmergencyRequest,
    current_user: User = Depends(get_current_user),
    controller: TradingController = Depends(get_controller),
):
    if body.confirm != "CONFIRM":
        raise HTTPException(status_code=400, detail='Must confirm with exact text "CONFIRM"')
    await controller.emergency_stop(body.account_id, user=current_user.email)
    return {"status": "emergency_stop_executed"}


@router.get("/status/{account_id}")
async def get_status(
    account_id: str,
    current_user: User = Depends(get_current_user),
    controller: TradingController = Depends(get_controller),
):
    status = await controller.get_status(account_id)
    return status.dict()


@router.get("/state-history/{account_id}")
async def get_state_history(
    account_id: str,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    redis=Depends(get_redis),
):
    from app.trading.state_machine import TradingStateMachine
    sm = TradingStateMachine(redis, account_id)
    history = await sm.get_history(limit=limit)
    return {"history": history}
