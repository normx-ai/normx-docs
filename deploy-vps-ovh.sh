#!/bin/bash

# Script de déploiement pour VPS OVH
# Pour docs.normx-ai.com et compta.normx-ai.com

set -e

echo "🚀 Déploiement de GD-IA-Comptable sur VPS OVH"
echo "=============================================="

# Variables
VPS_IP="51.83.75.203"
DOMAINS=("docs.normx-ai.com" "compta.normx-ai.com")

# Configuration PostgreSQL
echo "1️⃣ Configuration de PostgreSQL..."
sudo -u postgres psql << EOF
-- Créer l'utilisateur et la base de données
CREATE USER normx_docs_user WITH PASSWORD 'Normx2025Docs!';
CREATE DATABASE normx_docs_db OWNER normx_docs_user;
GRANT ALL PRIVILEGES ON DATABASE normx_docs_db TO normx_docs_user;
\q
EOF

# Création des répertoires
echo "2️⃣ Création de la structure..."
sudo mkdir -p /opt/normx/{docs,logs,uploads}
sudo mkdir -p /var/log/normx

# Clone du projet
echo "3️⃣ Clonage du projet..."
cd /opt/normx/docs
sudo git clone https://github.com/votre-compte/gd-ia-comptable.git . || echo "Dépôt déjà cloné"

# Configuration Python
echo "4️⃣ Configuration de l'environnement Python..."
sudo python3 -m venv venv
sudo ./venv/bin/pip install --upgrade pip
sudo ./venv/bin/pip install -r requirements.txt

# Configuration de production
echo "5️⃣ Création du fichier .env.production..."
sudo tee .env.production > /dev/null << 'EOF'
# Environment
ENV=production
DEBUG=false
ENVIRONMENT=production

# Base de données PostgreSQL
DATABASE_URL=postgresql://normx_docs_user:Normx2025Docs!@localhost:5432/normx_docs_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# Sécurité
SECRET_KEY=fKsP8zX4mN9qR2vT5hY7jB3nC6wE9aD1
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# CORS
CORS_ORIGINS=["https://docs.normx-ai.com","https://compta.normx-ai.com"]

# Hosts autorisés
ALLOWED_HOSTS=docs.normx-ai.com,compta.normx-ai.com

# Email
SMTP_HOST=ssl0.ovh.net
SMTP_PORT=465
SMTP_USER=contact@normx-ai.com
SMTP_PASSWORD=A_CONFIGURER
SMTP_FROM_EMAIL=noreply@normx-ai.com
SMTP_FROM_NAME=NormX Comptabilité

# Logs
LOG_LEVEL=INFO
LOG_FILE_PATH=/var/log/normx

# Uploads
UPLOAD_MAX_SIZE_MB=20
UPLOAD_DIRECTORY=/opt/normx/uploads
UPLOAD_ALLOWED_EXTENSIONS=.pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg

# 2FA
TWO_FACTOR_ISSUER=NormX Compta

# API
API_TIMEOUT=120
EOF

# Migrations
echo "6️⃣ Exécution des migrations..."
cd /opt/normx/docs
sudo ./venv/bin/alembic upgrade head

# Build du frontend
echo "7️⃣ Build du frontend React..."
cd /opt/normx/docs/frontend
sudo npm install
sudo npm run build

# Installation de serve globalement
sudo npm install -g serve

# Configuration Nginx
echo "8️⃣ Configuration Nginx..."
sudo tee /etc/nginx/sites-available/normx-docs << 'EOF'
# Redirection HTTP vers HTTPS
server {
    listen 80;
    server_name docs.normx-ai.com compta.normx-ai.com;
    return 301 https://$server_name$request_uri;
}

# Configuration HTTPS
server {
    listen 443 ssl http2;
    server_name docs.normx-ai.com compta.normx-ai.com;

    # Les certificats SSL seront ajoutés par Certbot
    
    # Headers de sécurité
    add_header X-Frame-Options "DENY";
    add_header X-Content-Type-Options "nosniff";
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Logs
    access_log /var/log/nginx/normx-docs.access.log;
    error_log /var/log/nginx/normx-docs.error.log;
    
    # Frontend React
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
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
    
    # Fichiers uploadés
    location /uploads {
        alias /opt/normx/uploads;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Activer le site
sudo ln -sf /etc/nginx/sites-available/normx-docs /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

# Services systemd
echo "9️⃣ Configuration des services systemd..."

# Service API
sudo tee /etc/systemd/system/normx-api.service > /dev/null << EOF
[Unit]
Description=NormX Docs API
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=ubuntu
WorkingDirectory=/opt/normx/docs
Environment="PATH=/opt/normx/docs/venv/bin"
Environment="ENV=production"
ExecStart=/opt/normx/docs/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Service Frontend
sudo tee /etc/systemd/system/normx-frontend.service > /dev/null << EOF
[Unit]
Description=NormX Docs Frontend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/normx/docs/frontend
Environment="NODE_ENV=production"
ExecStart=/usr/bin/serve -s build -l 3000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Service Celery Worker
sudo tee /etc/systemd/system/normx-celery-worker.service > /dev/null << EOF
[Unit]
Description=NormX Celery Worker
After=network.target redis.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/normx/docs
Environment="PATH=/opt/normx/docs/venv/bin"
Environment="ENV=production"
ExecStart=/opt/normx/docs/venv/bin/celery -A app.core.celery_app worker -l info
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Service Celery Beat
sudo tee /etc/systemd/system/normx-celery-beat.service > /dev/null << EOF
[Unit]
Description=NormX Celery Beat
After=network.target redis.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/normx/docs
Environment="PATH=/opt/normx/docs/venv/bin"
Environment="ENV=production"
ExecStart=/opt/normx/docs/venv/bin/celery -A app.core.celery_app beat -l info
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Permissions
echo "🔟 Configuration des permissions..."
sudo chown -R ubuntu:ubuntu /opt/normx
sudo chown -R ubuntu:ubuntu /var/log/normx

# Démarrage des services
echo "1️⃣1️⃣ Démarrage des services..."
sudo systemctl daemon-reload
sudo systemctl enable normx-api normx-frontend normx-celery-worker normx-celery-beat
sudo systemctl start normx-api normx-frontend normx-celery-worker normx-celery-beat

echo ""
echo "✅ Déploiement presque terminé!"
echo ""
echo "📋 Prochaine étape IMPORTANTE:"
echo ""
echo "Obtenir les certificats SSL (attendez la propagation DNS ~5-10 min):"
echo "sudo certbot --nginx -d docs.normx-ai.com -d compta.normx-ai.com"
echo ""
echo "📊 Vérification des services:"
echo "sudo systemctl status normx-api normx-frontend normx-celery-worker normx-celery-beat"
echo ""
echo "📝 Logs disponibles:"
echo "sudo journalctl -u normx-api -f"
echo "sudo journalctl -u normx-frontend -f"
echo ""
echo "🔐 N'oubliez pas de configurer le mot de passe SMTP dans .env.production!"