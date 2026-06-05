from app.tasks import celery_app
import structlog

log = structlog.get_logger()


@celery_app.task(name="app.tasks.notifications.send_emergency_alert_task")
def send_emergency_alert_task(account_id: str):
    from app.core.config import settings
    msg = f"🚨 EMERGENCY STOP triggered on QuantCore AI account {account_id}. All positions closed."
    _send_sms(msg)
    _send_email_alert(msg)
    log.critical("emergency_alert_sent", account=account_id)


@celery_app.task(name="app.tasks.notifications.send_risk_alert_task")
def send_risk_alert_task(account_id: str, alert_type: str, details: str):
    from app.core.config import settings
    msg = f"⚠️ QuantCore Risk Alert [{alert_type}] — Account {account_id}: {details}"
    _send_sms(msg)
    _send_email_alert(msg)


def _send_sms(message: str):
    try:
        from twilio.rest import Client
        from app.core.config import settings
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        # In production: fetch phone from user account
        client.messages.create(body=message, from_=settings.TWILIO_FROM_NUMBER, to="+10000000000")
    except Exception as e:
        log.warning("sms_send_failed", error=str(e))


def _send_email_alert(message: str):
    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail
        from app.core.config import settings
        sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        mail = Mail(
            from_email=settings.SENDGRID_FROM_EMAIL,
            to_emails=settings.SENDGRID_FROM_EMAIL,
            subject="QuantCore AI Alert",
            html_content=f"<p>{message}</p>",
        )
        sg.send(mail)
    except Exception as e:
        log.warning("email_alert_failed", error=str(e))
