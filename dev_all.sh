#!/bin/bash

# Script pour démarrer tous les services de développement NormX Docs

echo "🚀 Démarrage de l'environnement de développement NormX Docs..."

# Couleurs pour les messages
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Fonction pour vérifier si un service est en cours d'exécution
check_service() {
    if pgrep -f "$1" > /dev/null; then
        echo -e "${YELLOW}⚠️  $2 est déjà en cours d'exécution${NC}"
        return 1
    fi
    return 0
}

# Fonction pour tuer un processus par pattern
kill_by_pattern() {
    pkill -f "$1" 2>/dev/null
    sleep 1
}

# Arrêter les services existants si demandé
if [ "$1" = "--restart" ]; then
    echo -e "${BLUE}🔄 Arrêt des services existants...${NC}"
    kill_by_pattern "uvicorn app.main:app"
    kill_by_pattern "npm start"
    kill_by_pattern "celery.*worker"
    kill_by_pattern "celery.*beat"
    kill_by_pattern "redis-server"
    sleep 2
fi

# Créer les répertoires de logs s'ils n'existent pas
mkdir -p logs

# 1. Démarrer Redis
echo -e "${BLUE}1️⃣  Démarrage de Redis...${NC}"
if check_service "redis-server" "Redis"; then
    redis-server --daemonize yes
    sleep 2
    if pgrep -f "redis-server" > /dev/null; then
        echo -e "${GREEN}✅ Redis démarré${NC}"
    else
        echo -e "${RED}❌ Échec du démarrage de Redis${NC}"
        exit 1
    fi
fi

# 2. Activer l'environnement virtuel et installer les dépendances
echo -e "${BLUE}2️⃣  Configuration de l'environnement Python...${NC}"
if [ ! -d "venv" ]; then
    echo "Création de l'environnement virtuel..."
    python3 -m venv venv
fi

source venv/bin/activate

# Vérifier les dépendances Python
echo "Vérification des dépendances Python..."
pip install -q -r requirements.txt 2>/dev/null || echo -e "${YELLOW}⚠️  Certaines dépendances peuvent manquer${NC}"

# 3. Démarrer l'API FastAPI
echo -e "${BLUE}3️⃣  Démarrage de l'API FastAPI...${NC}"
if check_service "uvicorn app.main:app" "FastAPI"; then
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > logs/api.log 2>&1 &
    API_PID=$!
    sleep 3
    if kill -0 $API_PID 2>/dev/null; then
        echo -e "${GREEN}✅ API FastAPI démarrée sur http://localhost:8000${NC}"
        echo -e "   📖 Documentation: http://localhost:8000/docs"
    else
        echo -e "${RED}❌ Échec du démarrage de l'API${NC}"
        exit 1
    fi
fi

# 4. Démarrer Celery Worker
echo -e "${BLUE}4️⃣  Démarrage de Celery Worker...${NC}"
if check_service "celery.*worker" "Celery Worker"; then
    celery -A app.core.celery_config worker --loglevel=info > logs/celery_worker.log 2>&1 &
    WORKER_PID=$!
    sleep 2
    if kill -0 $WORKER_PID 2>/dev/null; then
        echo -e "${GREEN}✅ Celery Worker démarré${NC}"
    else
        echo -e "${RED}❌ Échec du démarrage de Celery Worker${NC}"
    fi
fi

# 5. Démarrer Celery Beat
echo -e "${BLUE}5️⃣  Démarrage de Celery Beat (Scheduler)...${NC}"
if check_service "celery.*beat" "Celery Beat"; then
    celery -A app.core.celery_config beat --loglevel=info > logs/celery_beat.log 2>&1 &
    BEAT_PID=$!
    sleep 2
    if kill -0 $BEAT_PID 2>/dev/null; then
        echo -e "${GREEN}✅ Celery Beat démarré${NC}"
    else
        echo -e "${RED}❌ Échec du démarrage de Celery Beat${NC}"
    fi
fi

# 6. Démarrer le Frontend React
echo -e "${BLUE}6️⃣  Démarrage du Frontend React...${NC}"
cd frontend
if [ ! -d "node_modules" ]; then
    echo "Installation des dépendances npm..."
    npm install
fi

if check_service "npm start" "Frontend React"; then
    npm start > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    cd ..
    sleep 5
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "${GREEN}✅ Frontend React démarré sur http://localhost:3000${NC}"
    else
        echo -e "${RED}❌ Échec du démarrage du Frontend${NC}"
    fi
else
    cd ..
fi

# Résumé
echo -e "\n${GREEN}🎉 Environnement de développement NormX Docs prêt !${NC}"
echo -e "\n📍 URLs des services :"
echo -e "   - Frontend: ${BLUE}http://localhost:3000${NC}"
echo -e "   - API: ${BLUE}http://localhost:8000${NC}"
echo -e "   - API Docs: ${BLUE}http://localhost:8000/docs${NC}"
echo -e "   - Redis: ${BLUE}localhost:6379${NC}"

echo -e "\n📁 Logs disponibles dans :"
echo -e "   - API: logs/api.log"
echo -e "   - Frontend: logs/frontend.log"
echo -e "   - Celery Worker: logs/celery_worker.log"
echo -e "   - Celery Beat: logs/celery_beat.log"

echo -e "\n🛑 Pour arrêter tous les services :"
echo -e "   ${YELLOW}pkill -f 'uvicorn|npm start|celery|redis-server'${NC}"

echo -e "\n🔄 Pour redémarrer tous les services :"
echo -e "   ${YELLOW}./dev_all.sh --restart${NC}"

# Garder le script actif et afficher les logs en temps réel
echo -e "\n📊 Surveillance des logs (Ctrl+C pour quitter)..."
echo -e "${YELLOW}Astuce: Ouvrez de nouveaux terminaux pour interagir avec l'application${NC}\n"

# Fonction pour nettoyer à la sortie
cleanup() {
    echo -e "\n${YELLOW}🛑 Arrêt des services...${NC}"
    kill_by_pattern "uvicorn app.main:app"
    kill_by_pattern "npm start"
    kill_by_pattern "celery.*worker"
    kill_by_pattern "celery.*beat"
    echo -e "${GREEN}✅ Services arrêtés${NC}"
    exit 0
}

# Capturer Ctrl+C
trap cleanup INT

# Afficher les logs en temps réel
tail -f logs/*.log