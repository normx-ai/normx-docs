#!/bin/bash
# Script pour démarrer Celery Beat (planificateur)

echo "🕐 Démarrage de Celery Beat..."

# Se placer dans le répertoire du projet
cd /home/chris/gd-ia-comptable

# Activer l'environnement virtuel
source venv/bin/activate

# Démarrer Celery Beat
celery -A app.core.celery_app beat \
    --loglevel=info \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler