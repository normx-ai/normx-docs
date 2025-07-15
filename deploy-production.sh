#!/bin/bash

# Script de déploiement en production pour OVH Performance
# Usage: ./deploy-production.sh

set -e

echo "🚀 Déploiement de NormX Docs en production"
echo "=========================================="

# Vérifications
if [ ! -f ".env.production" ]; then
    echo "❌ Erreur: Le fichier .env.production n'existe pas!"
    echo "Créez-le en copiant .env.production.example et en modifiant les valeurs"
    exit 1
fi

# Charger les variables d'environnement
export $(cat .env.production | grep -v '^#' | xargs)

echo "1️⃣ Installation des dépendances Python..."
source venv/bin/activate || python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

echo "2️⃣ Build du frontend React..."
cd frontend
npm install
npm run build
cd ..

echo "3️⃣ Exécution des migrations de base de données..."
ENV=production alembic upgrade head

echo "4️⃣ Collecte des fichiers statiques..."
mkdir -p static/uploads

echo "5️⃣ Test de configuration..."
ENV=production python -c "from app.core.config import settings; print('✅ Configuration OK')"

echo "6️⃣ Création des répertoires nécessaires..."
sudo mkdir -p /var/log/gd-ia-comptable
sudo mkdir -p /var/lib/gd-ia-comptable/uploads
sudo chown -R $USER:$USER /var/log/gd-ia-comptable
sudo chown -R $USER:$USER /var/lib/gd-ia-comptable

echo "7️⃣ Configuration des services systemd..."

# API Service
sudo tee /etc/systemd/system/gd-api.service > /dev/null << EOF
[Unit]
Description=GD IA Comptable API
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=$USER
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin"
Environment="ENV=production"
EnvironmentFile=$(pwd)/.env.production
ExecStart=$(pwd)/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Frontend Service
sudo tee /etc/systemd/system/gd-frontend.service > /dev/null << EOF
[Unit]
Description=GD IA Comptable Frontend
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)/frontend
Environment="NODE_ENV=production"
ExecStart=/usr/bin/serve -s build -l 3000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Celery Worker Service
sudo tee /etc/systemd/system/gd-celery-worker.service > /dev/null << EOF
[Unit]
Description=GD IA Comptable Celery Worker
After=network.target redis.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin"
Environment="ENV=production"
EnvironmentFile=$(pwd)/.env.production
ExecStart=$(pwd)/venv/bin/celery -A app.core.celery_app worker -l info
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Celery Beat Service
sudo tee /etc/systemd/system/gd-celery-beat.service > /dev/null << EOF
[Unit]
Description=GD IA Comptable Celery Beat
After=network.target redis.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin"
Environment="ENV=production"
EnvironmentFile=$(pwd)/.env.production
ExecStart=$(pwd)/venv/bin/celery -A app.core.celery_app beat -l info
Restart=always

[Install]
WantedBy=multi-user.target
EOF

echo "8️⃣ Installation de serve pour le frontend..."
sudo npm install -g serve

echo "9️⃣ Rechargement et démarrage des services..."
sudo systemctl daemon-reload
sudo systemctl enable gd-api gd-frontend gd-celery-worker gd-celery-beat
sudo systemctl restart gd-api gd-frontend gd-celery-worker gd-celery-beat

echo "🔟 Vérification des services..."
sleep 5
sudo systemctl status gd-api gd-frontend gd-celery-worker gd-celery-beat --no-pager

echo ""
echo "✅ Déploiement terminé!"
echo ""
echo "📊 Tableau de bord des services:"
echo "  - API: http://localhost:8000"
echo "  - Frontend: http://localhost:3000"
echo ""
echo "📝 Logs disponibles avec:"
echo "  - sudo journalctl -u gd-api -f"
echo "  - sudo journalctl -u gd-frontend -f"
echo "  - sudo journalctl -u gd-celery-worker -f"
echo "  - sudo journalctl -u gd-celery-beat -f"
echo ""
echo "⚡ Prochaine étape: Configurer Nginx avec SSL"
echo "   Voir PRODUCTION_DEPLOYMENT_GUIDE.md section 'Configuration Nginx avec SSL'"