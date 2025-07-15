# Guide de Déploiement sur OVH Performance

Ce guide détaille les étapes pour déployer l'application NormX Docs sur un serveur OVH Performance.

## Prérequis

### Serveur OVH Performance
- **OS recommandé** : Ubuntu 22.04 LTS
- **RAM minimum** : 8 GB
- **Stockage** : 50 GB SSD minimum
- **CPU** : 4 vCPU minimum

### Domaine et SSL
- Un nom de domaine pointant vers votre serveur OVH
- Certificat SSL (Let's Encrypt recommandé)

## Architecture de Déploiement

```
┌─────────────────────────────────────────────────────┐
│                   OVH Performance                    │
├─────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │   Nginx     │  │   Docker    │  │ PostgreSQL  │ │
│  │  (Reverse   │  │  Compose    │  │  Database   │ │
│  │   Proxy)    │  │             │  │             │ │
│  └─────────────┘  └─────────────┘  └─────────────┘ │
│                                                      │
│  ┌─────────────────────────────────────────────┐   │
│  │            Docker Containers                 │   │
│  ├─────────────┬─────────────┬────────────────┤   │
│  │  Frontend   │   Backend   │     Redis      │   │
│  │   (React)   │  (FastAPI)  │   (Cache)      │   │
│  └─────────────┴─────────────┴────────────────┘   │
└─────────────────────────────────────────────────────┘
```

## Étapes de Déploiement

### 1. Préparation du Serveur

#### 1.1 Connexion SSH
```bash
ssh root@votre-ip-ovh
```

#### 1.2 Mise à jour du système
```bash
apt update && apt upgrade -y
apt install -y curl git nginx certbot python3-certbot-nginx
```

#### 1.3 Installation de Docker
```bash
# Installation de Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Installation de Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

#### 1.4 Configuration du firewall
```bash
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
```

### 2. Déploiement de l'Application

#### 2.1 Cloner le repository
```bash
cd /opt
git clone https://github.com/votre-repo/gd-ia-comptable.git
cd gd-ia-comptable
```

#### 2.2 Configuration des variables d'environnement
```bash
# Créer le fichier .env de production
cat > .env.production << EOF
# Database
DATABASE_URL=postgresql://gd_user:CHANGE_THIS_PASSWORD@postgres:5432/gd_ia_comptable
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

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
CORS_ORIGINS=["https://votre-domaine.com"]

# Email (Configurez avec votre serveur SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=votre-email@gmail.com
SMTP_PASSWORD=votre-mot-de-passe-app
SMTP_FROM_EMAIL=noreply@votre-domaine.com
SMTP_FROM_NAME=NormX Docs

# Environment
ENV=production
DEBUG=false
EOF
```

#### 2.3 Créer docker-compose de production
```bash
# Le fichier sera créé dans l'étape suivante
```

### 3. Configuration Nginx

#### 3.1 Créer la configuration Nginx
```bash
cat > /etc/nginx/sites-available/normx-docs << 'EOF'
server {
    listen 80;
    server_name votre-domaine.com;
    
    # Redirection HTTP vers HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name votre-domaine.com;
    
    # SSL Configuration (sera ajouté par Certbot)
    
    # Logs
    access_log /var/log/nginx/normx-docs.access.log;
    error_log /var/log/nginx/normx-docs.error.log;
    
    # Taille maximale des uploads
    client_max_body_size 50M;
    
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
    
    # API Backend
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # WebSocket pour les notifications temps réel
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    # Documentation API
    location /docs {
        proxy_pass http://localhost:8000/docs;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /openapi.json {
        proxy_pass http://localhost:8000/openapi.json;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
}
EOF

# Activer le site
ln -s /etc/nginx/sites-available/normx-docs /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

#### 3.2 Configurer SSL avec Let's Encrypt
```bash
certbot --nginx -d votre-domaine.com
```

### 4. Lancement de l'Application

#### 4.1 Build et démarrage
```bash
cd /opt/gd-ia-comptable

# Construire les images
docker-compose -f docker-compose.production.yml build

# Démarrer les services
docker-compose -f docker-compose.production.yml up -d

# Vérifier les logs
docker-compose -f docker-compose.production.yml logs -f
```

#### 4.2 Initialisation de la base de données
```bash
# Exécuter les migrations
docker-compose -f docker-compose.production.yml exec backend alembic upgrade head

# Créer un utilisateur admin (optionnel)
docker-compose -f docker-compose.production.yml exec backend python -m scripts.create_admin
```

### 5. Configuration des Sauvegardes

#### 5.1 Sauvegarde automatique de la base de données
```bash
# Créer le script de sauvegarde
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

# Suppression des sauvegardes de plus de 30 jours
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

# Copie vers stockage distant (optionnel)
# rclone copy $BACKUP_DIR/db_backup_$DATE.sql.gz remote:backups/
EOF

chmod +x /opt/backup-normx.sh

# Ajouter au crontab
echo "0 2 * * * /opt/backup-normx.sh" | crontab -
```

### 6. Monitoring et Maintenance

#### 6.1 Surveillance des logs
```bash
# Logs de l'application
docker-compose -f docker-compose.production.yml logs -f

# Logs Nginx
tail -f /var/log/nginx/normx-docs.*.log

# Espace disque
df -h

# Utilisation mémoire
free -m
```

#### 6.2 Mise à jour de l'application
```bash
cd /opt/gd-ia-comptable
git pull origin main
docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml up -d
```

### 7. Sécurité Additionnelle

#### 7.1 Fail2ban
```bash
apt install fail2ban -y

# Configuration pour SSH
cat > /etc/fail2ban/jail.local << EOF
[sshd]
enabled = true
port = 22
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
EOF

systemctl restart fail2ban
```

#### 7.2 Surveillance automatique
```bash
# Installation de monitoring basique
apt install -y htop iotop nethogs
```

## Checklist de Déploiement

- [ ] Serveur OVH commandé et accessible
- [ ] Nom de domaine configuré (DNS)
- [ ] Docker et Docker Compose installés
- [ ] Repository cloné
- [ ] Variables d'environnement configurées
- [ ] Docker Compose de production créé
- [ ] Nginx configuré
- [ ] SSL/TLS activé
- [ ] Application démarrée
- [ ] Base de données initialisée
- [ ] Sauvegardes configurées
- [ ] Monitoring en place

## Dépannage

### Problèmes courants

1. **Erreur de connexion à la base de données**
   ```bash
   docker-compose -f docker-compose.production.yml logs postgres
   ```

2. **Application non accessible**
   ```bash
   # Vérifier que les conteneurs sont en cours d'exécution
   docker-compose -f docker-compose.production.yml ps
   
   # Vérifier Nginx
   systemctl status nginx
   ```

3. **Problèmes de permissions**
   ```bash
   chown -R 1000:1000 /opt/gd-ia-comptable
   ```

## Support

Pour toute question ou problème lors du déploiement, consultez :
- Les logs de l'application
- La documentation Docker Compose
- Les forums OVH