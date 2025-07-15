#!/usr/bin/env python
"""
Script pour démarrer le worker Celery
"""
import os
import sys

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.celery_config import celery_app

if __name__ == '__main__':
    celery_app.start()