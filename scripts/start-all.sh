#!/bin/bash

# Script pour démarrer TOUS les services (Backend + Frontend)

echo "🚀 Démarrage complet de l'application..."

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour arrêter tous les services
cleanup() {
    echo -e "\n${YELLOW}🛑 Arrêt de tous les services...${NC}"
    
    # Arrêter les processus
    pkill -f "celery -A app.core.celery_app"
    pkill -f "uvicorn app.main:app"
    pkill -f "npm start"
    
    # Arrêter les processus enfants
    jobs -p | xargs -r kill
    
    exit 0
}

# Capturer Ctrl+C
trap cleanup INT

# Vérifier si Redis est démarré
if ! pgrep -x "redis-server" > /dev/null
then
    echo -e "${YELLOW}📦 Démarrage de Redis...${NC}"
    redis-server --daemonize yes
    sleep 2
fi

# Activer l'environnement virtuel Python
source venv/bin/activate

# Créer les logs si nécessaire
mkdir -p logs

echo -e "${GREEN}✅ Redis démarré${NC}"

# Démarrer Celery Worker en arrière-plan
echo -e "${YELLOW}👷 Démarrage du worker Celery...${NC}"
celery -A app.core.celery_app worker --loglevel=info > logs/celery_worker.log 2>&1 &
WORKER_PID=$!

# Démarrer Celery Beat en arrière-plan
echo -e "${YELLOW}⏰ Démarrage du scheduler Celery Beat...${NC}"
celery -A app.core.celery_app beat --loglevel=info > logs/celery_beat.log 2>&1 &
BEAT_PID=$!

# Démarrer l'API FastAPI en arrière-plan
echo -e "${YELLOW}🌐 Démarrage de l'API Backend...${NC}"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > logs/api.log 2>&1 &
API_PID=$!

# Attendre que l'API soit prête
echo -e "${YELLOW}⏳ Attente du démarrage de l'API...${NC}"
sleep 5

# Démarrer le Frontend React
echo -e "${BLUE}🎨 Démarrage du Frontend React...${NC}"
cd frontend && npm start > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!

# Attendre un peu pour que tout démarre
sleep 5

echo -e "\n${GREEN}✅ Tous les services sont démarrés !${NC}"
echo -e "${GREEN}📍 Backend API: http://localhost:8000${NC}"
echo -e "${GREEN}📍 Backend Docs: http://localhost:8000/docs${NC}"
echo -e "${GREEN}📍 Frontend: http://localhost:3000${NC}"
echo -e "\n${YELLOW}📊 Logs disponibles dans le dossier ./logs/${NC}"
echo -e "${YELLOW}Appuyez sur Ctrl+C pour arrêter tous les services${NC}\n"

# Afficher les logs de l'API en temps réel
echo -e "${BLUE}📋 Logs de l'API :${NC}"
tail -f logs/api.log