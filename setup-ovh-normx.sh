#!/bin/bash

# Script de configuration pour normx-ai.com sur OVH
# Pour app.normx-ai.com et docs.normx-ai.com

set -e

echo "🚀 Configuration du serveur OVH pour NormX AI"
echo "============================================"

# Mise à jour du système
echo "1️⃣ Mise à jour du système..."
apt update && apt upgrade -y

# Installation des dépendances
echo "2️⃣ Installation des dépendances..."
apt install -y \
    python3-pip python3-venv python3-dev \
    postgresql postgresql-contrib \
    redis-server \
    nginx \
    certbot python3-certbot-nginx \
    nodejs npm \
    git \
    supervisor \
    ufw \
    fail2ban

# Configuration du firewall
echo "3️⃣ Configuration du firewall..."
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Création des utilisateurs système
echo "4️⃣ Création des utilisateurs..."
useradd -m -s /bin/bash normx-app || echo "Utilisateur existe déjà"
useradd -m -s /bin/bash normx-docs || echo "Utilisateur existe déjà"

# Structure des répertoires
echo "5️⃣ Création de la structure..."
mkdir -p /opt/normx-ai/app
mkdir -p /opt/normx-ai/docs
mkdir -p /var/log/normx-ai/app
mkdir -p /var/log/normx-ai/docs
mkdir -p /var/lib/normx-ai/app/uploads
mkdir -p /var/lib/normx-ai/docs/uploads

# PostgreSQL
echo "6️⃣ Configuration PostgreSQL..."
sudo -u postgres psql << EOF
-- Base pour app.normx-ai.com
CREATE USER normx_app_user WITH PASSWORD 'CHANGEZ_CE_MOT_DE_PASSE_APP';
CREATE DATABASE normx_app_db OWNER normx_app_user;
GRANT ALL PRIVILEGES ON DATABASE normx_app_db TO normx_app_user;

-- Base pour docs.normx-ai.com (GD-IA-Comptable)
CREATE USER normx_docs_user WITH PASSWORD 'CHANGEZ_CE_MOT_DE_PASSE_DOCS';
CREATE DATABASE normx_docs_db OWNER normx_docs_user;
GRANT ALL PRIVILEGES ON DATABASE normx_docs_db TO normx_docs_user;
EOF

# Configuration Nginx pour app.normx-ai.com
echo "7️⃣ Configuration Nginx pour app.normx-ai.com..."
cat > /etc/nginx/sites-available/app.normx-ai.com << 'EOF'
server {
    listen 80;
    server_name app.normx-ai.com;
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name app.normx-ai.com;
    
    # SSL sera configuré par Certbot
    
    # Headers de sécurité
    add_header X-Frame-Options "DENY";
    add_header X-Content-Type-Options "nosniff";
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    location / {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    location /api {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Configuration Nginx pour docs.normx-ai.com
echo "8️⃣ Configuration Nginx pour docs.normx-ai.com..."
cat > /etc/nginx/sites-available/docs.normx-ai.com << 'EOF'
server {
    listen 80;
    server_name docs.normx-ai.com;
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name docs.normx-ai.com;
    
    # SSL sera configuré par Certbot
    
    # Headers de sécurité
    add_header X-Frame-Options "DENY";
    add_header X-Content-Type-Options "nosniff";
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Frontend React
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    # API FastAPI
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # WebSocket
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

# Activer les sites
echo "9️⃣ Activation des sites..."
ln -sf /etc/nginx/sites-available/app.normx-ai.com /etc/nginx/sites-enabled/
ln -sf /etc/nginx/sites-available/docs.normx-ai.com /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx
nginx -t

echo "🔟 Redémarrage de Nginx..."
systemctl restart nginx

# Permissions
chown -R normx-app:normx-app /opt/normx-ai/app
chown -R normx-docs:normx-docs /opt/normx-ai/docs
chown -R normx-app:normx-app /var/log/normx-ai/app
chown -R normx-docs:normx-docs /var/log/normx-ai/docs
chown -R normx-app:normx-app /var/lib/normx-ai/app
chown -R normx-docs:normx-docs /var/lib/normx-ai/docs

echo ""
echo "✅ Configuration initiale terminée!"
echo ""
echo "📋 Prochaines étapes:"
echo ""
echo "1. Obtenir les certificats SSL:"
echo "   certbot --nginx -d app.normx-ai.com"
echo "   certbot --nginx -d docs.normx-ai.com"
echo ""
echo "2. Déployer l'application principale dans /opt/normx-ai/app"
echo ""
echo "3. Déployer GD-IA-Comptable dans /opt/normx-ai/docs:"
echo "   cd /opt/normx-ai/docs"
echo "   git clone https://github.com/votre-compte/gd-ia-comptable.git ."
echo "   chown -R normx-docs:normx-docs ."
echo ""
echo "4. Configurer les fichiers .env.production pour chaque application"
echo ""
echo "🔐 IMPORTANT: Changez les mots de passe PostgreSQL dans ce script!"