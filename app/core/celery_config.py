from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "normx_docs",
    broker=settings.REDIS_URL or "redis://localhost:6379/0",
    backend=settings.REDIS_URL or "redis://localhost:6379/0",
    include=["app.tasks.notifications", "app.tasks.reminders"]
)

# Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Paris",
    enable_utc=True,
)

# Tâches planifiées
celery_app.conf.beat_schedule = {
    # Vérifier les échéances tous les matins à 8h
    "check-deadlines-morning": {
        "task": "app.tasks.reminders.check_deadlines",
        "schedule": crontab(hour=8, minute=0),
    },
    # Vérifier les dossiers urgents toutes les heures
    "check-urgent-dossiers": {
        "task": "app.tasks.reminders.check_urgent_dossiers",
        "schedule": crontab(minute=0),
    },
    # Envoyer un rapport quotidien à 18h
    "daily-report": {
        "task": "app.tasks.reminders.send_daily_report",
        "schedule": crontab(hour=18, minute=0),
    },
    # Vérifier les retards toutes les 30 minutes
    "check-overdue": {
        "task": "app.tasks.reminders.check_overdue_dossiers",
        "schedule": crontab(minute="*/30"),
    },
}