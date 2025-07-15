#!/bin/bash

# Script de déploiement automatisé pour OVH Performance
# Usage: ./scripts/deploy-to-ovh.sh [options]

set -e  # Exit on error

# Configuration
REMOTE_HOST=""
REMOTE_USER="root"
REMOTE_PATH="/opt/gd-ia-comptable"
BRANCH="main"

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Fonction d'aide
show_help() {
    echo "Usage: $0 -h <host> [-u <user>] [-p <path>] [-b <branch>]"
    echo ""
    echo "Options:"
    echo "  -h <host>    Adresse IP ou hostname du serveur OVH (requis)"
    echo "  -u <user>    Utilisateur SSH (défaut: root)"
    echo "  -p <path>    Chemin distant (défaut: /opt/gd-ia-comptable)"
    echo "  -b <branch>  Branche git à déployer (défaut: main)"
    echo "  --help       Afficher cette aide"
    exit 0
}

# Parser les arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--host)
            REMOTE_HOST="$2"
            shift 2
            ;;
        -u|--user)
            REMOTE_USER="$2"
            shift 2
            ;;
        -p|--path)
            REMOTE_PATH="$2"
            shift 2
            ;;
        -b|--branch)
            BRANCH="$2"
            shift 2
            ;;
        --help)
            show_help
            ;;
        *)
            echo -e "${RED}Option inconnue: $1${NC}"
            show_help
            ;;
    esac
done

# Vérifier les paramètres requis
if [ -z "$REMOTE_HOST" ]; then
    echo -e "${RED}Erreur: L'hôte distant (-h) est requis${NC}"
    show_help
fi

# Fonction pour exécuter des commandes à distance
remote_exec() {
    ssh "${REMOTE_USER}@${REMOTE_HOST}" "$@"
}

# Fonction pour copier des fichiers
remote_copy() {
    scp "$1" "${REMOTE_USER}@${REMOTE_HOST}:$2"
}

echo -e "${BLUE}=== Déploiement sur OVH Performance ===${NC}"
echo -e "Hôte: ${REMOTE_HOST}"
echo -e "Utilisateur: ${REMOTE_USER}"
echo -e "Chemin: ${REMOTE_PATH}"
echo -e "Branche: ${BRANCH}"
echo ""

# 1. Vérifier la connexion SSH
echo -e "${BLUE}1. Vérification de la connexion SSH...${NC}"
if remote_exec "echo 'Connexion SSH OK'"; then
    echo -e "${GREEN}✓ Connexion SSH établie${NC}"
else
    echo -e "${RED}✗ Impossible de se connecter au serveur${NC}"
    exit 1
fi

# 2. Vérifier que Docker est installé
echo -e "${BLUE}2. Vérification de Docker...${NC}"
if remote_exec "docker --version && docker-compose --version" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Docker et Docker Compose sont installés${NC}"
else
    echo -e "${YELLOW}⚠ Docker n'est pas installé. Installation...${NC}"
    remote_exec "curl -fsSL https://get.docker.com | sh"
    remote_exec "curl -L 'https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)' -o /usr/local/bin/docker-compose && chmod +x /usr/local/bin/docker-compose"
fi

# 3. Préparer le répertoire de destination
echo -e "${BLUE}3. Préparation du répertoire...${NC}"
remote_exec "mkdir -p ${REMOTE_PATH}"

# 4. Copier les fichiers de configuration
echo -e "${BLUE}4. Copie des fichiers de configuration...${NC}"
remote_copy "docker-compose.production.yml" "${REMOTE_PATH}/"
remote_copy "Dockerfile.production" "${REMOTE_PATH}/Dockerfile"
remote_copy "frontend/Dockerfile.production" "${REMOTE_PATH}/frontend/Dockerfile"

# 5. Créer le fichier .env.production s'il n'existe pas
echo -e "${BLUE}5. Configuration de l'environnement...${NC}"
if ! remote_exec "test -f ${REMOTE_PATH}/.env.production"; then
    echo -e "${YELLOW}Création du fichier .env.production...${NC}"
    remote_exec "cat > ${REMOTE_PATH}/.env.production << 'EOF'
# Database
DATABASE_URL=postgresql://gd_user:CHANGE_THIS_PASSWORD@postgres:5432/gd_ia_comptable
DB_PASSWORD=CHANGE_THIS_PASSWORD

# Security
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Redis
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# API
API_URL=https://votre-domaine.com
CORS_ORIGINS=[\"https://votre-domaine.com\"]

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=noreply@votre-domaine.com
SMTP_FROM_NAME=NormX Docs

# Environment
ENV=production
DEBUG=false
EOF"
    echo -e "${YELLOW}⚠ IMPORTANT: Modifiez ${REMOTE_PATH}/.env.production avec vos valeurs${NC}"
fi

# 6. Pull/Clone du repository
echo -e "${BLUE}6. Mise à jour du code source...${NC}"
if remote_exec "test -d ${REMOTE_PATH}/.git"; then
    echo "Repository existant, mise à jour..."
    remote_exec "cd ${REMOTE_PATH} && git fetch origin && git checkout ${BRANCH} && git pull origin ${BRANCH}"
else
    echo "Clonage du repository..."
    REPO_URL=$(git config --get remote.origin.url)
    remote_exec "cd $(dirname ${REMOTE_PATH}) && git clone ${REPO_URL} $(basename ${REMOTE_PATH})"
    remote_exec "cd ${REMOTE_PATH} && git checkout ${BRANCH}"
fi

# 7. Construire et démarrer les conteneurs
echo -e "${BLUE}7. Construction et démarrage des conteneurs...${NC}"
remote_exec "cd ${REMOTE_PATH} && docker-compose -f docker-compose.production.yml build"
remote_exec "cd ${REMOTE_PATH} && docker-compose -f docker-compose.production.yml down"
remote_exec "cd ${REMOTE_PATH} && docker-compose -f docker-compose.production.yml up -d"

# 8. Attendre que les services soient prêts
echo -e "${BLUE}8. Attente du démarrage des services...${NC}"
sleep 10

# 9. Exécuter les migrations
echo -e "${BLUE}9. Exécution des migrations...${NC}"
remote_exec "cd ${REMOTE_PATH} && docker-compose -f docker-compose.production.yml exec -T backend alembic upgrade head"

# 10. Vérifier l'état des services
echo -e "${BLUE}10. Vérification des services...${NC}"
remote_exec "cd ${REMOTE_PATH} && docker-compose -f docker-compose.production.yml ps"

# 11. Afficher les logs récents
echo -e "${BLUE}11. Logs récents:${NC}"
remote_exec "cd ${REMOTE_PATH} && docker-compose -f docker-compose.production.yml logs --tail=20"

echo -e "${GREEN}=== Déploiement terminé avec succès! ===${NC}"
echo -e ""
echo -e "Prochaines étapes:"
echo -e "1. Configurez Nginx sur le serveur pour le reverse proxy"
echo -e "2. Configurez SSL avec Let's Encrypt"
echo -e "3. Modifiez ${REMOTE_PATH}/.env.production avec vos valeurs"
echo -e "4. Configurez les sauvegardes automatiques"
echo -e ""
echo -e "Pour voir les logs en temps réel:"
echo -e "ssh ${REMOTE_USER}@${REMOTE_HOST} 'cd ${REMOTE_PATH} && docker-compose -f docker-compose.production.yml logs -f'"