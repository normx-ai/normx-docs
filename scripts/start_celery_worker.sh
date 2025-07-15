#!/bin/bash
# Script pour démarrer le worker Celery

echo "🚀 Démarrage du worker Celery..."

# Se placer dans le répertoire du projet
cd /home/chris/gd-ia-comptable

# Activer l'environnement virtuel
source venv/bin/activate

# Démarrer le worker avec plusieurs queues
celery -A app.core.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --queues=notifications,emails,maintenance \
    --hostname=worker@%h \
    --max-tasks-per-child=1000