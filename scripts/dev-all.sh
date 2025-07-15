#!/bin/bash

# Script de développement pour démarrer TOUT (Backend + Frontend)

echo "🚀 Démarrage complet de l'application Cabinet Comptable..."
echo ""

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Fonction pour arrêter tous les services
stop_all() {
    echo -e "${YELLOW}Arrêt des services...${NC}"
    
    # Arrêter le frontend
    pkill -f "npm start"
    pkill -f "react-scripts start"
    
    # Arrêter le backend
    pkill -f "uvicorn app.main:app"
    
    # Arrêter Celery
    pkill -f "celery -A app.core.celery_app worker"
    pkill -f "celery -A app.core.celery_app beat"
    
    # Attendre un peu pour que tout s'arrête
    sleep 2
}

# Fonction de nettoyage à la sortie
cleanup() {
    echo -e "\n${YELLOW}Arrêt en cours...${NC}"
    stop_all
    exit 0
}

trap cleanup INT

# Vérifier si --restart est passé en paramètre
if [ "$1" == "--restart" ]; then
    echo -e "${YELLOW}Redémarrage des services...${NC}"
    stop_all
fi

# Vérifier Redis
if ! pgrep -x "redis-server" > /dev/null; then
    echo "📦 Démarrage de Redis..."
    redis-server --daemonize yes
    sleep 1
else
    echo -e "${GREEN}✓${NC} Redis déjà en cours d'exécution"
fi

# Activer l'environnement virtuel
echo "🐍 Activation de l'environnement virtuel..."
source venv/bin/activate

# Créer les répertoires nécessaires
mkdir -p logs
mkdir -p uploads
mkdir -p templates/emails

# Vérifier la base de données
echo "🗄️  Vérification de la base de données..."
if ! venv/bin/alembic current 2>/dev/null | grep -q "head"; then
    echo "  Application des migrations..."
    venv/bin/alembic upgrade head
fi

# Backend - API
echo "🔧 Démarrage du backend API..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > logs/api.log 2>&1 &
BACKEND_PID=$!

# Attendre que le backend soit prêt
echo "  Attente du démarrage de l'API..."
for i in {1..10}; do
    if curl -s http://localhost:8000/api/v1/health > /dev/null; then
        echo -e "  ${GREEN}✓${NC} API prête"
        break
    fi
    sleep 1
done

# Celery Worker
echo "⚙️  Démarrage de Celery Worker..."
celery -A app.core.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --queues=notifications,emails,maintenance \
    > logs/celery_worker.log 2>&1 &
WORKER_PID=$!
echo -e "  ${GREEN}✓${NC} Worker démarré"

# Celery Beat
echo "🕐 Démarrage de Celery Beat..."
celery -A app.core.celery_app beat \
    --loglevel=info \
    > logs/celery_beat.log 2>&1 &
BEAT_PID=$!
echo -e "  ${GREEN}✓${NC} Beat démarré"

# Frontend
echo "🎨 Démarrage du frontend..."
cd frontend
npm start > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Attendre un peu
sleep 3

# Afficher le statut
echo -e "\n${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Application démarrée avec succès !${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo ""
echo -e "📋 Services actifs:"
echo -e "  ${GREEN}•${NC} Backend API : http://localhost:8000"
echo -e "  ${GREEN}•${NC} Documentation : http://localhost:8000/docs"
echo -e "  ${GREEN}•${NC} Frontend : http://localhost:3000"
echo -e "  ${GREEN}•${NC} Redis : localhost:6379"
echo ""
echo -e "📊 Monitoring:"
echo -e "  ${GREEN}•${NC} Logs API : tail -f logs/api.log"
echo -e "  ${GREEN}•${NC} Logs Worker : tail -f logs/celery_worker.log"
echo -e "  ${GREEN}•${NC} Logs Beat : tail -f logs/celery_beat.log"
echo -e "  ${GREEN}•${NC} Logs Frontend : tail -f logs/frontend.log"
echo ""
echo -e "🛠️  Commandes utiles:"
echo -e "  ${GREEN}•${NC} Redémarrer : ./scripts/dev-all.sh --restart"
echo -e "  ${GREEN}•${NC} Tester notifications : venv/bin/python scripts/test_notifications.py"
echo -e "  ${GREEN}•${NC} État Celery : celery -A app.core.celery_app inspect active"
echo ""
echo -e "${YELLOW}Ctrl+C pour arrêter tous les services${NC}"
echo ""

# Garder le script actif et afficher les logs importants
tail -f logs/api.log | grep -E "(ERROR|WARNING|Started)" &

# Attendre
wait