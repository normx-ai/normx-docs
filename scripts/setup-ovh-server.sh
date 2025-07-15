#!/bin/bash

# Script de configuration initiale du serveur OVH
# À exécuter sur le serveur OVH après une installation fraîche

set -e

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=== Configuration du serveur OVH pour NormX Docs ===${NC}"

# 1. Mise à jour du système
echo -e "${BLUE}1. Mise à jour du système...${NC}"
apt update && apt upgrade -y

# 2. Installation des paquets essentiels
echo -e "${BLUE}2. Installation des paquets essentiels...${NC}"
apt install -y \
    curl \
    git \
    nginx \
    certbot \
    python3-certbot-nginx \
    ufw \
    fail2ban \
    htop \
    iotop \
    nethogs \
    ncdu \
    vim \
    tmux

# 3. Configuration du firewall
echo -e "${BLUE}3. Configuration du firewall...${NC}"
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# 4. Installation de Docker
echo -e "${BLUE}4. Installation de Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
else
    echo -e "${GREEN}Docker déjà installé${NC}"
fi

# 5. Installation de Docker Compose
echo -e "${BLUE}5. Installation de Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
else
    echo -e "${GREEN}Docker Compose déjà installé${NC}"
fi

# 6. Configuration de fail2ban
echo -e "${BLUE}6. Configuration de fail2ban...${NC}"
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log

[nginx-noscript]
enabled = true
port = http,https
filter = nginx-noscript
logpath = /var/log/nginx/access.log
maxretry = 6

[nginx-badbots]
enabled = true
port = http,https
filter = nginx-badbots
logpath = /var/log/nginx/access.log
maxretry = 2

[nginx-noproxy]
enabled = true
port = http,https
filter = nginx-noproxy
logpath = /var/log/nginx/access.log
maxretry = 2
EOF

systemctl restart fail2ban

# 7. Création des répertoires
echo -e "${BLUE}7. Création des répertoires...${NC}"
mkdir -p /opt/gd-ia-comptable
mkdir -p /opt/backups/normx-docs
mkdir -p /var/log/normx-docs

# 8. Configuration des limites système
echo -e "${BLUE}8. Configuration des limites système...${NC}"
cat >> /etc/security/limits.conf << 'EOF'

# Limites pour NormX Docs
* soft nofile 65536
* hard nofile 65536
* soft nproc 32768
* hard nproc 32768
EOF

# 9. Optimisation sysctl
echo -e "${BLUE}9. Optimisation des paramètres système...${NC}"
cat > /etc/sysctl.d/99-normx-docs.conf << 'EOF'
# Optimisations réseau pour NormX Docs
net.core.somaxconn = 65536
net.ipv4.tcp_max_syn_backlog = 65536
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 30
net.core.netdev_max_backlog = 65536

# Optimisations mémoire
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5
EOF

sysctl -p /etc/sysctl.d/99-normx-docs.conf

# 10. Configuration de journald
echo -e "${BLUE}10. Configuration de la rotation des logs...${NC}"
cat > /etc/systemd/journald.conf.d/50-default.conf << 'EOF'
[Journal]
SystemMaxUse=1G
SystemKeepFree=1G
SystemMaxFileSize=100M
MaxRetentionSec=30day
EOF

systemctl restart systemd-journald

# 11. Installation de monitoring basique
echo -e "${BLUE}11. Configuration du monitoring...${NC}"
# Netdata (optionnel mais recommandé)
read -p "Installer Netdata pour le monitoring? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    bash <(curl -Ss https://my-netdata.io/kickstart.sh) --dont-wait
fi

# 12. Configuration SSH renforcée
echo -e "${BLUE}12. Renforcement de la configuration SSH...${NC}"
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup
cat >> /etc/ssh/sshd_config << 'EOF'

# Renforcement de la sécurité SSH
Protocol 2
PermitRootLogin yes  # Changez en 'no' après avoir configuré un utilisateur
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2
AllowUsers root  # Ajoutez vos utilisateurs autorisés
EOF

systemctl restart sshd

# 13. Création d'un utilisateur dédié (optionnel)
echo -e "${BLUE}13. Création d'un utilisateur dédié...${NC}"
read -p "Créer un utilisateur dédié 'normx'? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    useradd -m -s /bin/bash normx
    usermod -aG docker normx
    echo "Définissez le mot de passe pour l'utilisateur normx:"
    passwd normx
    
    # Ajout aux sudoers
    echo "normx ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/normx
fi

# 14. Script de sauvegarde
echo -e "${BLUE}14. Installation du script de sauvegarde...${NC}"
cat > /opt/backup-normx.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups/normx-docs"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Sauvegarde de la base de données
docker-compose -f /opt/gd-ia-comptable/docker-compose.production.yml exec -T postgres \
    pg_dump -U gd_user gd_ia_comptable > $BACKUP_DIR/db_backup_$DATE.sql

# Compression
gzip $BACKUP_DIR/db_backup_$DATE.sql

# Sauvegarde des uploads
tar czf $BACKUP_DIR/uploads_backup_$DATE.tar.gz -C /opt/gd-ia-comptable uploads/

# Suppression des sauvegardes de plus de 30 jours
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Sauvegarde terminée: $DATE"
EOF

chmod +x /opt/backup-normx.sh

# Ajout au crontab
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/backup-normx.sh >> /var/log/normx-docs/backup.log 2>&1") | crontab -

# 15. Informations finales
echo -e "${GREEN}=== Configuration terminée! ===${NC}"
echo -e ""
echo -e "Informations système:"
docker --version
docker-compose --version
nginx -v
echo -e ""
echo -e "${YELLOW}Prochaines étapes:${NC}"
echo -e "1. Clonez le repository dans /opt/gd-ia-comptable"
echo -e "2. Configurez le fichier .env.production"
echo -e "3. Lancez le déploiement avec docker-compose"
echo -e "4. Configurez Nginx et SSL"
echo -e ""
echo -e "${YELLOW}Sécurité:${NC}"
echo -e "- Changez PermitRootLogin à 'no' dans /etc/ssh/sshd_config"
echo -e "- Configurez des clés SSH pour l'authentification"
echo -e "- Mettez à jour régulièrement le système"
echo -e ""
echo -e "${GREEN}Le serveur est prêt pour le déploiement de NormX Docs!${NC}"