from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "quantcore",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.reports", "app.tasks.notifications"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="America/New_York",
    enable_utc=True,
    beat_schedule={
        "daily-report-0700": {
            "task": "app.tasks.reports.generate_daily_reports",
            "schedule": "0 7 * * *",  # crontab(hour=7, minute=0)
        },
        "weekly-report-monday-0800": {
            "task": "app.tasks.reports.generate_weekly_reports",
            "schedule": "0 8 * * 1",
        },
        "monthly-report-1st-0800": {
            "task": "app.tasks.reports.generate_monthly_reports",
            "schedule": "0 8 1 * *",
        },
    },
)
