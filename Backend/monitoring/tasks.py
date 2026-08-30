from celery import shared_task
from .email import EmergencyEmailService

@shared_task(bind=True, max_retries=3, default_retry_delay=5, time_limit=10)
def send_async_critical_alert(email_target, device_name, heart_rate, oxygen_level, timestamp):

    print(f"[CELERY TASK] Starting asynchronous email delivery to {email_target}...")
    
    success = EmergencyEmailService.send_critical_alert(
        email_target=email_target,
        device_name=device_name,
        heart_rate=heart_rate,
        oxygen_level=oxygen_level,
        timestamp=timestamp
    )
    
    if success:
        print(f"[CELERY TASK] Email sent successfully via worker.")
    else:
        print(f"[CELERY TASK] Email delivery failed in worker.")