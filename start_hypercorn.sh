#!/bin/bash
# Script de démarrage Hypercorn

# Activer l'environnement virtuel
source venv/bin/activate

# Variables d'environnement pour développement local
export DATABASE_URL="postgresql://postgres@localhost:5432/gd_ia_comptable"
export ENV="development"

echo "Démarrage de Hypercorn sur http://0.0.0.0:8000"
hypercorn app.main:app --bind 0.0.0.0:8000 --access-log --error-log --reload