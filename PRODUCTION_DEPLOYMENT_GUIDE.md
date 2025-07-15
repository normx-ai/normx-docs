# 🚀 Guide de Déploiement en Production - NormX Docs

## 📋 Prérequis

### 1. Serveur OVH Performance
- Ubuntu 22.04 LTS
- Minimum 4GB RAM
- 2 vCPU
- 40GB SSD

### 2. Domaine configuré
- Domaine pointant vers l'IP du serveur
- Certificat SSL (Let's Encrypt)

## 🔧 Étapes de Déploiement

### 1️⃣ Configuration du serveur

```bash
# Se connecter au serveur
ssh root@VOTRE_IP_OVH

# Exécuter le script de configuration
curl -fsSL https://raw.githubusercontent.com/votrecompte/gd-ia-comptable/main/scripts/setup-ovh-server.sh | bash
```

### 2️⃣ Variables d'environnement de production

Créer le fichier `.env.production` :

```bash
cat > /opt/gd-ia-comptable/.env.production << 'EOF'
# Environment
ENV=production
DEBUG=false
ENVIRONMENT=production

# Base de données PostgreSQL
DATABASE_URL=postgresql://gd_prod_user:VOTRE_MOT_DE_PASSE_SECURISE@localhost:5432/gd_ia_comptable_prod
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# Sécurité - GÉNÉRER UNE NOUVELLE CLÉ !
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# CORS - Remplacer par votre domaine
CORS_ORIGINS=["https://votre-domaine.com","https://www.votre-domaine.com"]
ALLOWED_HOSTS=votre-domaine.com,www.votre-domaine.com

# Email - Configurer avec votre service
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=votre-email@gmail.com
SMTP_PASSWORD=votre-mot-de-passe-app
SMTP_FROM_EMAIL=noreply@votre-domaine.com
SMTP_FROM_NAME=NormX Docs

# Logs
LOG_LEVEL=INFO
LOG_FILE_PATH=/var/log/gd-ia-comptable

# Uploads
UPLOAD_MAX_SIZE_MB=20
UPLOAD_DIRECTORY=/var/lib/gd-ia-comptable/uploads
UPLOAD_ALLOWED_EXTENSIONS=.pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg

# 2FA
TWO_FACTOR_ISSUER=NormX Docs

# API
API_TIMEOUT=120
EOF
```

### 3️⃣ Configuration de la base de données

```bash
# Créer l'utilisateur et la base de données PostgreSQL
sudo -u postgres psql << EOF
CREATE USER gd_prod_user WITH PASSWORD 'VOTRE_MOT_DE_PASSE_SECURISE';
CREATE DATABASE gd_ia_comptable_prod OWNER gd_prod_user;
GRANT ALL PRIVILEGES ON DATABASE gd_ia_comptable_prod TO gd_prod_user;
EOF

# Exécuter les migrations
cd /opt/gd-ia-comptable
source venv/bin/activate
alembic upgrade head
```

### 4️⃣ Configuration Nginx avec SSL

```bash
# Configuration Nginx
sudo tee /etc/nginx/sites-available/gd-ia-comptable << 'EOF'
server {
    listen 80;
    server_name votre-domaine.com www.votre-domaine.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name votre-domaine.com www.votre-domaine.com;

    ssl_certificate /etc/letsencrypt/live/votre-domaine.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/votre-domaine.com/privkey.pem;
    
    # Configuration SSL sécurisée
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
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
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
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
    
    # Fichiers statiques
    location /uploads {
        alias /var/lib/gd-ia-comptable/uploads;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Activer le site
sudo ln -s /etc/nginx/sites-available/gd-ia-comptable /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 5️⃣ Certificat SSL avec Let's Encrypt

```bash
# Installer Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtenir le certificat
sudo certbot --nginx -d votre-domaine.com -d www.votre-domaine.com
```

### 6️⃣ Services Systemd

#### Service API
```bash
sudo tee /etc/systemd/system/gd-api.service << 'EOF'
[Unit]
Description=GD IA Comptable API
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=gd-app
Group=gd-app
WorkingDirectory=/opt/gd-ia-comptable
Environment="PATH=/opt/gd-ia-comptable/venv/bin"
Environment="ENV=production"
ExecStart=/opt/gd-ia-comptable/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

#### Service Frontend
```bash
sudo tee /etc/systemd/system/gd-frontend.service << 'EOF'
[Unit]
Description=GD IA Comptable Frontend
After=network.target

[Service]
Type=simple
User=gd-app
Group=gd-app
WorkingDirectory=/opt/gd-ia-comptable/frontend
Environment="NODE_ENV=production"
Environment="REACT_APP_API_URL=https://votre-domaine.com"
ExecStart=/usr/bin/npm run start:production
Restart=always

[Install]
WantedBy=multi-user.target
EOF
```

#### Service Celery Worker
```bash
sudo tee /etc/systemd/system/gd-celery-worker.service << 'EOF'
[Unit]
Description=GD IA Comptable Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=gd-app
Group=gd-app
WorkingDirectory=/opt/gd-ia-comptable
Environment="PATH=/opt/gd-ia-comptable/venv/bin"
Environment="ENV=production"
ExecStart=/opt/gd-ia-comptable/venv/bin/celery -A app.core.celery_app worker -l info -D
Restart=always

[Install]
WantedBy=multi-user.target
EOF
```

#### Service Celery Beat
```bash
sudo tee /etc/systemd/system/gd-celery-beat.service << 'EOF'
[Unit]
Description=GD IA Comptable Celery Beat
After=network.target redis.service

[Service]
Type=simple
User=gd-app
Group=gd-app
WorkingDirectory=/opt/gd-ia-comptable
Environment="PATH=/opt/gd-ia-comptable/venv/bin"
Environment="ENV=production"
ExecStart=/opt/gd-ia-comptable/venv/bin/celery -A app.core.celery_app beat -l info
Restart=always

[Install]
WantedBy=multi-user.target
EOF
```

### 7️⃣ Démarrage des services

```bash
# Recharger systemd
sudo systemctl daemon-reload

# Activer et démarrer tous les services
sudo systemctl enable --now gd-api gd-frontend gd-celery-worker gd-celery-beat

# Vérifier le statut
sudo systemctl status gd-api gd-frontend gd-celery-worker gd-celery-beat
```

### 8️⃣ Création du premier cabinet et admin

```bash
cd /opt/gd-ia-comptable
source venv/bin/activate
python << EOF
from app.core.database import SessionLocal
from app.models.cabinet import Cabinet
from app.models.user import User
from app.core.security import get_password_hash

db = SessionLocal()

# Créer le premier cabinet
cabinet = Cabinet(
    nom="Cabinet Principal",
    slug="cabinet-principal",
    email="contact@votre-domaine.com",
    pays_code="FR",
    devise="EUR",
    plan="premium"
)
db.add(cabinet)
db.commit()

# Créer l'utilisateur admin
admin = User(
    cabinet_id=cabinet.id,
    username="admin",
    email="admin@votre-domaine.com",
    hashed_password=get_password_hash("CHANGEZ_CE_MOT_DE_PASSE"),
    full_name="Administrateur",
    role="admin",
    is_active=True
)
db.add(admin)
db.commit()

print(f"✅ Cabinet créé: {cabinet.nom} (ID: {cabinet.id})")
print(f"✅ Admin créé: {admin.email}")
print("⚠️  N'oubliez pas de changer le mot de passe!")
EOF
```

## 📊 Monitoring

### Logs
```bash
# API
sudo journalctl -u gd-api -f

# Frontend
sudo journalctl -u gd-frontend -f

# Celery
sudo journalctl -u gd-celery-worker -f
sudo journalctl -u gd-celery-beat -f

# Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Monitoring avec Prometheus (optionnel)
```bash
# Ajouter dans requirements.txt
prometheus-client==0.19.0
prometheus-fastapi-instrumentator==6.1.0

# Configuration dans app/main.py
from prometheus_fastapi_instrumentator import Instrumentator

# Après app = FastAPI()
Instrumentator().instrument(app).expose(app)
```

## 🔒 Sécurité Post-Déploiement

### 1. Firewall
```bash
# Configurer UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
```

### 2. Fail2ban
```bash
# Installer et configurer Fail2ban
sudo apt install fail2ban -y

# Configuration pour l'API
sudo tee /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[nginx-limit-req]
enabled = true
EOF

sudo systemctl restart fail2ban
```

### 3. Backups automatiques
```bash
# Script de backup
sudo tee /opt/gd-ia-comptable/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/gd-ia-comptable"
DATE=$(date +%Y%m%d_%H%M%S)

# Créer le répertoire de backup
mkdir -p $BACKUP_DIR

# Backup de la base de données
pg_dump -U gd_prod_user gd_ia_comptable_prod > $BACKUP_DIR/db_$DATE.sql

# Backup des uploads
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz /var/lib/gd-ia-comptable/uploads

# Garder seulement les 7 derniers jours
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
EOF

chmod +x /opt/gd-ia-comptable/backup.sh

# Ajouter au cron
(crontab -l ; echo "0 2 * * * /opt/gd-ia-comptable/backup.sh") | crontab -
```

## ✅ Checklist Finale

- [ ] Variables d'environnement configurées
- [ ] Base de données PostgreSQL créée et migrations exécutées
- [ ] Redis en cours d'exécution
- [ ] Certificat SSL installé
- [ ] Services systemd actifs
- [ ] Firewall configuré
- [ ] Backups automatiques configurés
- [ ] Premier cabinet et admin créés
- [ ] Tests de connexion réussis
- [ ] Monitoring opérationnel

## 🆘 Dépannage

### L'API ne démarre pas
```bash
# Vérifier les logs
sudo journalctl -u gd-api -n 100 --no-pager

# Tester manuellement
cd /opt/gd-ia-comptable
source venv/bin/activate
ENV=production uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Erreurs de permission
```bash
# Corriger les permissions
sudo chown -R gd-app:gd-app /opt/gd-ia-comptable
sudo chown -R gd-app:gd-app /var/lib/gd-ia-comptable
sudo chown -R gd-app:gd-app /var/log/gd-ia-comptable
```

### Base de données inaccessible
```bash
# Vérifier PostgreSQL
sudo systemctl status postgresql
sudo -u postgres psql -c "\l"
```

## 📞 Support

Pour toute assistance :
- Documentation : https://votre-domaine.com/docs
- Email : support@votre-domaine.com