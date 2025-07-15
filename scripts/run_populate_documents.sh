#!/bin/bash

# Script pour exécuter la population des documents requis
# avec activation automatique de l'environnement virtuel

set -e  # Arrêter en cas d'erreur

echo "=== SCRIPT DE POPULATION DES DOCUMENTS REQUIS ==="

# Changer vers le répertoire du projet
cd "$(dirname "$0")/.."

# Vérifier si l'environnement virtuel existe
if [ ! -d "venv" ]; then
    echo "❌ Erreur: l'environnement virtuel 'venv' n'existe pas."
    echo "Créez-le d'abord avec: python3 -m venv venv"
    exit 1
fi

# Activer l'environnement virtuel
echo "🔄 Activation de l'environnement virtuel..."
source venv/bin/activate

# Vérifier les dépendances
echo "🔄 Vérification des dépendances..."
if ! python -c "import sqlalchemy" 2>/dev/null; then
    echo "❌ SQLAlchemy n'est pas installé. Installation..."
    pip install -r requirements.txt
fi

# Exécuter selon les arguments
case "${1:-}" in
    "test")
        echo "🧪 Exécution du test de simulation (dry-run)..."
        python scripts/test_populate_dry_run.py
        ;;
    "verify")
        echo "🔍 Vérification des documents requis existants..."
        python scripts/populate_documents_requis.py --verify
        ;;
    "details")
        echo "📋 Affichage des détails des documents requis..."
        python scripts/populate_documents_requis.py --details
        ;;
    "force")
        echo "⚠️  Exécution avec force (recréation)..."
        read -p "Êtes-vous sûr? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            python scripts/populate_documents_requis.py --force
        else
            echo "Opération annulée."
            exit 1
        fi
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [option]"
        echo ""
        echo "Options:"
        echo "  (aucune)  Exécuter la population normale"
        echo "  test      Exécuter le test de simulation"
        echo "  verify    Vérifier les documents existants"
        echo "  details   Afficher les détails des documents"
        echo "  force     Forcer la recréation (avec confirmation)"
        echo "  help      Afficher cette aide"
        echo ""
        echo "Exemples:"
        echo "  $0              # Population normale"
        echo "  $0 test         # Test de simulation"
        echo "  $0 verify       # Vérification seulement"
        echo "  $0 details      # Affichage détaillé"
        exit 0
        ;;
    "")
        echo "🚀 Exécution de la population des documents requis..."
        python scripts/populate_documents_requis.py
        ;;
    *)
        echo "❌ Option inconnue: $1"
        echo "Utilisez '$0 help' pour voir les options disponibles."
        exit 1
        ;;
esac

echo "✅ Opération terminée!"

# Désactiver l'environnement virtuel
deactivate