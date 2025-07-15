# Guide de Déploiement en Production

## Vue d'ensemble

Ce guide couvre le déploiement complet de l'application Cabinet Comptable en production, avec support multi-pays OHADA.

## Prérequis

### 1. Serveur
- Ubuntu 20.04 LTS ou plus récent
- Minimum 4GB RAM, 2 CPU
- 50GB stockage SSD
- Accès SSH root ou sudo

### 2. Domaine
- Nom de domaine configuré (ex: cabinet-comptable.com)
- Accès DNS pour configuration

### 3. Services externes
- Compte SMTP pour envoi d'emails
- Backup externe (S3, Backblaze, etc.)

## Architecture de Production

```
                    ┌─────────────┐
                    │   Nginx     │
                    │  (HTTPS)    │
                    └──────┬──────┘
                           │
                ┌──────────┴──────────┐
                │                     │
          ┌─────▼─────┐        ┌─────▼─────┐
          │  FastAPI  │        │   React   │
          │   :8000   │        │   :3000   │
          └─────┬─────┘        └───────────┘
                │
     ┌──────────┼──────────┐
     │          │          │
┌────▼────┐ ┌──▼──┐ ┌─────▼─────┐
│PostgreSQL│ │Redis│ │  Celery   │
│  :5432   │ │:6379│ │Worker/Beat│
└──────────┘ └─────┘ └───────────┘
```

## Étapes de Déploiement

### 1. Préparation du Serveur

```bash
# Mise à jour système
sudo apt update && sudo apt upgrade -y

# Installation des dépendances
sudo apt install -y python3.9 python3.9-venv python3-pip \
    postgresql postgresql-contrib \
    redis-server nginx git \
    certbot python3-certbot-nginx \
    build-essential libpq-dev

# Node.js pour React
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Créer utilisateur application
sudo adduser --system --group cabinet
```

### 2. Configuration PostgreSQL

```bash
# Accéder à PostgreSQL
sudo -u postgres psql

# Créer la base de données
CREATE DATABASE cabinet_comptable;
CREATE USER cabinet_user WITH ENCRYPTED PASSWORD 'CHANGER_CE_MOT_DE_PASSE';
GRANT ALL PRIVILEGES ON DATABASE cabinet_comptable TO cabinet_user;
\q

# Configurer PostgreSQL pour production
sudo nano /etc/postgresql/12/main/postgresql.conf
# Ajuster: max_connections = 200
# shared_buffers = 256MB
```

### 3. Configuration Redis

```bash
# Sécuriser Redis
sudo nano /etc/redis/redis.conf

# Ajouter/modifier:
requirepass CHANGER_CE_MOT_DE_PASSE
maxmemory 512mb
maxmemory-policy allkeys-lru

# Redémarrer
sudo systemctl restart redis-server
```

### 4. Déploiement de l'Application

```bash
# Cloner le repository
cd /opt
sudo git clone https://github.com/votre-repo/cabinet-comptable.git
sudo chown -R cabinet:cabinet cabinet-comptable
cd cabinet-comptable

# Environnement virtuel Python
sudo -u cabinet python3.9 -m venv venv
sudo -u cabinet venv/bin/pip install --upgrade pip
sudo -u cabinet venv/bin/pip install -r requirements.txt

# Configuration production
sudo -u cabinet cp .env.example .env.production
sudo nano .env.production
```

### 5. Configuration .env Production

```bash
# Configuration de base
ENV=production
DEBUG=False

# Base de données
DATABASE_URL=postgresql://cabinet_user:MOT_DE_PASSE@localhost:5432/cabinet_comptable
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# JWT et Sécurité
SECRET_KEY=GENERER_AVEC_SCRIPT_generate_secret_key.py
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis
REDIS_URL=redis://:MOT_DE_PASSE@localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://:MOT_DE_PASSE@localhost:6379/1
CELERY_RESULT_BACKEND=redis://:MOT_DE_PASSE@localhost:6379/2

# Email SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=votre-email@gmail.com
SMTP_PASSWORD=mot-de-passe-application
SMTP_FROM_EMAIL=noreply@cabinet-comptable.com
SMTP_FROM_NAME=Cabinet Comptable
SMTP_TLS=True
SMTP_SSL=False

# CORS
CORS_ORIGINS=["https://cabinet-comptable.com","https://www.cabinet-comptable.com"]

# Domaine
FRONTEND_URL=https://cabinet-comptable.com
API_URL=https://cabinet-comptable.com/api

# Logs
LOG_LEVEL=INFO
LOG_FILE=/var/log/cabinet/app.log
```

### 6. Migrations Base de Données

```bash
# Appliquer les migrations
sudo -u cabinet venv/bin/alembic upgrade head

# Créer le premier cabinet (optionnel)
sudo -u cabinet venv/bin/python scripts/create_default_cabinet.py
```

### 7. Build Frontend

```bash
cd frontend
sudo -u cabinet npm install
sudo -u cabinet npm run build
```

### 8. Configuration Systemd

#### Service API
```bash
sudo nano /etc/systemd/system/cabinet-api.service
```

```ini
[Unit]
Description=Cabinet Comptable API
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=cabinet
Group=cabinet
WorkingDirectory=/opt/cabinet-comptable
Environment="PATH=/opt/cabinet-comptable/venv/bin"
EnvironmentFile=/opt/cabinet-comptable/.env.production
ExecStart=/opt/cabinet-comptable/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Service Celery Worker
```bash
sudo nano /etc/systemd/system/cabinet-celery-worker.service
```

```ini
[Unit]
Description=Cabinet Celery Worker
After=network.target redis.service

[Service]
Type=exec
User=cabinet
Group=cabinet
WorkingDirectory=/opt/cabinet-comptable
Environment="PATH=/opt/cabinet-comptable/venv/bin"
EnvironmentFile=/opt/cabinet-comptable/.env.production
ExecStart=/opt/cabinet-comptable/venv/bin/celery -A app.core.celery_app worker --loglevel=info --concurrency=4 --queues=notifications,emails,maintenance
Restart=always

[Install]
WantedBy=multi-user.target
```

#### Service Celery Beat
```bash
sudo nano /etc/systemd/system/cabinet-celery-beat.service
```

```ini
[Unit]
Description=Cabinet Celery Beat
After=network.target redis.service

[Service]
Type=exec
User=cabinet
Group=cabinet
WorkingDirectory=/opt/cabinet-comptable
Environment="PATH=/opt/cabinet-comptable/venv/bin"
EnvironmentFile=/opt/cabinet-comptable/.env.production
ExecStart=/opt/cabinet-comptable/venv/bin/celery -A app.core.celery_app beat --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
```

### 9. Démarrer les Services

```bash
# Recharger systemd
sudo systemctl daemon-reload

# Démarrer et activer les services
sudo systemctl enable --now cabinet-api
sudo systemctl enable --now cabinet-celery-worker
sudo systemctl enable --now cabinet-celery-beat

# Vérifier le statut
sudo systemctl status cabinet-api
sudo systemctl status cabinet-celery-worker
sudo systemctl status cabinet-celery-beat
```

### 10. Configuration Nginx

```bash
sudo nano /etc/nginx/sites-available/cabinet-comptable
```

Utiliser la configuration du fichier `docs/HTTPS_CONFIG.md`

```bash
# Activer le site
sudo ln -s /etc/nginx/sites-available/cabinet-comptable /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 11. SSL avec Let's Encrypt

```bash
sudo certbot --nginx -d cabinet-comptable.com -d www.cabinet-comptable.com
```

## Monitoring et Maintenance

### 1. Logs

```bash
# Créer répertoire logs
sudo mkdir -p /var/log/cabinet
sudo chown cabinet:cabinet /var/log/cabinet

# Rotation des logs
sudo nano /etc/logrotate.d/cabinet
```

```
/var/log/cabinet/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 cabinet cabinet
}
```

### 2. Monitoring avec Prometheus

```bash
# Installation
sudo apt install prometheus prometheus-node-exporter

# Configuration pour FastAPI
pip install prometheus-fastapi-instrumentator
```

### 3. Backups Automatiques

```bash
sudo nano /opt/cabinet-comptable/scripts/backup.sh
```

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/cabinet"

# Backup PostgreSQL
pg_dump cabinet_comptable | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup uploads
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz /opt/cabinet-comptable/uploads

# Nettoyer les anciens backups (garder 30 jours)
find $BACKUP_DIR -type f -mtime +30 -delete

# Synchroniser vers stockage externe (exemple S3)
aws s3 sync $BACKUP_DIR s3://bucket-backups/cabinet/ --delete
```

```bash
# Cron pour backup quotidien
sudo crontab -e
0 2 * * * /opt/cabinet-comptable/scripts/backup.sh
```

## Sécurité Production

### 1. Firewall

```bash
# UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### 2. Fail2ban

```bash
sudo apt install fail2ban
sudo nano /etc/fail2ban/jail.local
```

```ini
[sshd]
enabled = true
maxretry = 3

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
maxretry = 10
findtime = 60
bantime = 3600
```

### 3. Sécurité Application

- Activer tous les headers de sécurité dans Nginx
- Limiter les taux de requêtes
- Scanner régulièrement les vulnérabilités
- Mettre à jour les dépendances

## Performance

### 1. Optimisations PostgreSQL

```sql
-- Index pour les requêtes fréquentes
CREATE INDEX idx_dossiers_cabinet_mois ON dossiers(cabinet_id, mois, annee);
CREATE INDEX idx_documents_dossier ON documents(dossier_id, type_document);
CREATE INDEX idx_users_cabinet ON users(cabinet_id);
```

### 2. Cache Redis

- Sessions utilisateurs
- Résultats de requêtes fréquentes
- Compteurs de notifications

### 3. CDN pour Assets

Utiliser Cloudflare ou autre CDN pour :
- Fichiers statiques React
- Images et documents
- Protection DDoS

## Checklist de Lancement

- [ ] Serveur configuré et sécurisé
- [ ] PostgreSQL en production
- [ ] Redis sécurisé
- [ ] Application déployée
- [ ] Services systemd actifs
- [ ] Nginx + HTTPS configuré
- [ ] Backups automatiques
- [ ] Monitoring actif
- [ ] Tests de charge effectués
- [ ] Documentation mise à jour
- [ ] Plan de reprise d'activité

## Support Multi-Pays

Pour chaque pays OHADA :
- Vérifier les fuseaux horaires
- Tester les validations
- Configurer les emails en français local
- Adapter les formats de dates/devises

## Commandes Utiles

```bash
# Logs en temps réel
sudo journalctl -u cabinet-api -f
sudo journalctl -u cabinet-celery-worker -f

# Redémarrer services
sudo systemctl restart cabinet-api
sudo systemctl restart cabinet-celery-worker

# État des services
sudo systemctl status cabinet-*

# Mise à jour
cd /opt/cabinet-comptable
sudo -u cabinet git pull
sudo -u cabinet venv/bin/pip install -r requirements.txt
sudo -u cabinet venv/bin/alembic upgrade head
sudo systemctl restart cabinet-api
```