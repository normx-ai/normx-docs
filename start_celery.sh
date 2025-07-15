#!/bin/bash

# Script pour démarrer Celery Worker et Celery Beat

echo "Démarrage de Redis..."
redis-server --daemonize yes

echo "Activation de l'environnement virtuel..."
source venv/bin/activate

echo "Démarrage de Celery Worker..."
celery -A app.core.celery_config worker --loglevel=info &

echo "Démarrage de Celery Beat..."
celery -A app.core.celery_config beat --loglevel=info &

echo "Celery est maintenant en cours d'exécution"
echo "Pour arrêter : pkill -f celery"