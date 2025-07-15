"""
Configuration Celery pour les tâches asynchrones
"""

import os
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Créer l'instance Celery
celery_app = Celery(
    "cabinet_comptable",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks"]
)

# Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Paris",
    enable_utc=True,
    result_expires=3600,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Configuration des tâches planifiées
celery_app.conf.beat_schedule = {
    # Vérification des notifications tous les jours à 9h
    "check-notifications-morning": {
        "task": "app.tasks.check_all_notifications",
        "schedule": crontab(hour=9, minute=0),
        "options": {"queue": "notifications"}
    },
    
    # Vérification supplémentaire à 14h pour les urgences
    "check-notifications-afternoon": {
        "task": "app.tasks.check_all_notifications",
        "schedule": crontab(hour=14, minute=0),
        "options": {"queue": "notifications"}
    },
    
    # Rappel hebdomadaire le lundi matin
    "weekly-summary": {
        "task": "app.tasks.send_weekly_summary",
        "schedule": crontab(hour=8, minute=0, day_of_week=1),  # Lundi
        "options": {"queue": "notifications"}
    },
    
    # Nettoyage des anciennes notifications (tous les dimanches à 2h)
    "cleanup-old-notifications": {
        "task": "app.tasks.cleanup_old_notifications",
        "schedule": crontab(hour=2, minute=0, day_of_week=0),  # Dimanche
        "options": {"queue": "maintenance"}
    },
    
    # Mise à jour des statuts des échéances (tous les jours à minuit)
    "update-echeances-status": {
        "task": "app.tasks.update_echeances_status",
        "schedule": crontab(hour=0, minute=5),
        "options": {"queue": "maintenance"}
    },
}

# Routing des tâches vers différentes queues
celery_app.conf.task_routes = {
    "app.tasks.check_all_notifications": {"queue": "notifications"},
    "app.tasks.send_notification_email": {"queue": "emails"},
    "app.tasks.send_weekly_summary": {"queue": "notifications"},
    "app.tasks.cleanup_old_notifications": {"queue": "maintenance"},
    "app.tasks.update_echeances_status": {"queue": "maintenance"},
}