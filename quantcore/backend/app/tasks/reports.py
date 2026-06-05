"""
Celery tasks for scheduled and on-demand report generation.
"""
from app.tasks import celery_app
import structlog

log = structlog.get_logger()


@celery_app.task(name="app.tasks.reports.generate_report_task", bind=True, max_retries=3)
def generate_report_task(
    self,
    account_id: str,
    report_type: str,
    from_date: str | None = None,
    to_date: str | None = None,
    strategies: list | None = None,
    delivery: list | None = None,
    user_email: str | None = None,
):
    try:
        from app.reports.generator import ReportGenerator
        import asyncio
        from app.core.database import AsyncSessionLocal
        from sqlalchemy import select, and_
        from app.models.trade import Trade, TradeStatus
        from datetime import datetime

        gen = ReportGenerator()
        trades_data = []
        metrics = {}

        # Fetch trades synchronously for Celery
        pdf_bytes = getattr(gen, f"generate_{report_type}")(account_id, trades_data, metrics)

        # Upload to S3
        _upload_to_s3(account_id, report_type, pdf_bytes)

        # Deliver
        if delivery and "email" in delivery and user_email:
            _send_email_report(user_email, report_type, pdf_bytes)

        log.info("report_generated", account=account_id, type=report_type)
        return {"status": "success", "account_id": account_id, "type": report_type}

    except Exception as exc:
        log.error("report_generation_failed", error=str(exc), account=account_id)
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="app.tasks.reports.generate_daily_reports")
def generate_daily_reports():
    log.info("scheduled_daily_reports_starting")
    # In production: query all active accounts and fire individual tasks
    pass


@celery_app.task(name="app.tasks.reports.generate_weekly_reports")
def generate_weekly_reports():
    log.info("scheduled_weekly_reports_starting")
    pass


@celery_app.task(name="app.tasks.reports.generate_monthly_reports")
def generate_monthly_reports():
    log.info("scheduled_monthly_reports_starting")
    pass


def _upload_to_s3(account_id: str, report_type: str, pdf_bytes: bytes):
    try:
        import boto3
        from app.core.config import settings
        from datetime import datetime
        key = f"reports/{account_id}/{report_type}/{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        s3 = boto3.client("s3", region_name=settings.AWS_REGION)
        s3.put_object(Bucket=settings.S3_BUCKET_REPORTS, Key=key, Body=pdf_bytes, ContentType="application/pdf")
    except Exception as e:
        log.warning("s3_upload_failed", error=str(e))


def _send_email_report(email: str, report_type: str, pdf_bytes: bytes):
    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
        import base64
        from app.core.config import settings
        sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        message = Mail(
            from_email=settings.SENDGRID_FROM_EMAIL,
            to_emails=email,
            subject=f"QuantCore AI — {report_type.title()} Report",
            html_content=f"<p>Your {report_type} trading report is attached.</p>",
        )
        attachment = Attachment(
            FileContent(base64.b64encode(pdf_bytes).decode()),
            FileName(f"quantcore_{report_type}_report.pdf"),
            FileType("application/pdf"),
            Disposition("attachment"),
        )
        message.attachment = attachment
        sg.send(message)
    except Exception as e:
        log.warning("email_send_failed", error=str(e))
