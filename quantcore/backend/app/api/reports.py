from fastapi import APIRouter, Depends, BackgroundTasks, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from datetime import date
import structlog

from app.api.auth import get_current_user
from app.models.account import User

log = structlog.get_logger()
router = APIRouter(prefix="/reports", tags=["reports"])


class GenerateReportRequest(BaseModel):
    account_id: str
    report_type: str  # "daily" | "weekly" | "monthly" | "custom"
    from_date: date | None = None
    to_date: date | None = None
    strategies: list[str] | None = None
    delivery: list[str] = ["dashboard"]  # "dashboard" | "email" | "sms"


@router.post("/generate")
async def generate_report(
    body: GenerateReportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    from app.tasks.reports import generate_report_task
    task = generate_report_task.delay(
        account_id=body.account_id,
        report_type=body.report_type,
        from_date=str(body.from_date) if body.from_date else None,
        to_date=str(body.to_date) if body.to_date else None,
        strategies=body.strategies,
        delivery=body.delivery,
        user_email=current_user.email,
    )
    return {"task_id": task.id, "status": "queued"}


@router.get("/list/{account_id}")
async def list_reports(
    account_id: str,
    limit: int = Query(20, le=100),
    current_user: User = Depends(get_current_user),
):
    # In production: query S3/DB for generated report list
    return {"reports": [], "account_id": account_id}


@router.get("/download/{report_id}")
async def download_report(report_id: str, current_user: User = Depends(get_current_user)):
    # In production: fetch from S3 and return as FileResponse
    raise NotImplementedError("Report download from S3 not yet implemented")
