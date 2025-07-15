#!/bin/bash

# Script pour exécuter la migration des saisies PAIE

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== MIGRATION DES SAISIES PAIE ==="

cd "$PROJECT_DIR"

# Vérification de l'environnement virtuel
if [ ! -d "venv" ]; then
    echo "❌ Environnement virtuel 'venv' non trouvé"
    exit 1
fi

echo "🔄 Activation de l'environnement virtuel..."
source venv/bin/activate

# Vérification préliminaire
echo "🔍 Vérification préliminaire..."
python scripts/migrate_paie_saisies.py --verify

echo ""
echo "📋 Exécution de la migration..."
python scripts/migrate_paie_saisies.py

echo ""
echo "✅ Migration terminée!"