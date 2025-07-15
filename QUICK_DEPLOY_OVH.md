# 🚀 Déploiement Rapide sur OVH Performance

## 📋 Prérequis
- Serveur OVH Performance avec Ubuntu 22.04
- Accès SSH root
- Domaine configuré pointant vers l'IP du serveur

## 🏃 Déploiement en 10 minutes

### 1. Connexion au serveur
```bash
ssh root@VOTRE_IP_OVH
```

### 2. Installation automatique
```bash
# Cloner le projet
cd /opt
git clone https://github.com/votre-compte/gd-ia-comptable.git
cd gd-ia-comptable

# Installer les dépendances système
apt update && apt upgrade -y
apt install -y python3-pip python3-venv postgresql postgresql-contrib redis-server nginx certbot python3-certbot-nginx nodejs npm

# Créer l'utilisateur système
useradd -m -s /bin/bash gd-app
chown -R gd-app:gd-app /opt/gd-ia-comptable
```

### 3. Configuration PostgreSQL
```bash
# Créer la base de données
sudo -u postgres psql << EOF
CREATE USER gd_prod_user WITH PASSWORD 'CHANGER_CE_MOT_DE_PASSE';
CREATE DATABASE gd_ia_comptable_prod OWNER gd_prod_user;
GRANT ALL PRIVILEGES ON DATABASE gd_ia_comptable_prod TO gd_prod_user;
EOF
```

### 4. Configuration de l'application
```bash
# Copier et éditer la configuration
cp .env.production.example .env.production
nano .env.production

# Modifier au minimum :
# - SECRET_KEY (générer avec: python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
# - DATABASE_URL (avec le mot de passe PostgreSQL)
# - CORS_ORIGINS (avec votre domaine)
# - ALLOWED_HOSTS (avec votre domaine)
# - Configuration SMTP
```

### 5. Déploiement automatique
```bash
# Exécuter le script de déploiement
su - gd-app
cd /opt/gd-ia-comptable
./deploy-production.sh
```

### 6. Configuration Nginx + SSL
```bash
# Retour en root
exit

# Configuration Nginx
cat > /etc/nginx/sites-available/gd-ia-comptable << 'EOF'
server {
    listen 80;
    server_name VOTRE_DOMAINE.com www.VOTRE_DOMAINE.com;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

# Activer le site
ln -s /etc/nginx/sites-available/gd-ia-comptable /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

# Obtenir le certificat SSL
certbot --nginx -d VOTRE_DOMAINE.com -d www.VOTRE_DOMAINE.com
```

### 7. Créer le premier cabinet et admin
```bash
su - gd-app
cd /opt/gd-ia-comptable
source venv/bin/activate

python << EOF
from app.core.database import SessionLocal
from app.models.cabinet import Cabinet
from app.models.user import User
from app.core.security import get_password_hash

db = SessionLocal()

# Cabinet
cabinet = Cabinet(
    nom="Mon Cabinet",
    slug="mon-cabinet",
    email="contact@VOTRE_DOMAINE.com",
    pays_code="FR",
    devise="EUR"
)
db.add(cabinet)
db.commit()

# Admin
admin = User(
    cabinet_id=cabinet.id,
    username="admin",
    email="admin@VOTRE_DOMAINE.com",
    hashed_password=get_password_hash("CHANGER_CE_MOT_DE_PASSE"),
    full_name="Administrateur",
    role="admin",
    is_active=True
)
db.add(admin)
db.commit()

print("✅ Cabinet et admin créés!")
EOF
```

## ✅ Vérification

1. Accéder à https://VOTRE_DOMAINE.com
2. Se connecter avec l'admin créé
3. Changer immédiatement le mot de passe

## 📊 Monitoring

```bash
# Statut des services
systemctl status gd-api gd-frontend gd-celery-worker gd-celery-beat

# Logs en temps réel
journalctl -u gd-api -f
journalctl -u gd-frontend -f
```

## 🔧 Dépannage

Si l'API ne démarre pas :
```bash
# Vérifier les logs
journalctl -u gd-api -n 50

# Test manuel
su - gd-app
cd /opt/gd-ia-comptable
source venv/bin/activate
ENV=production python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 🎉 C'est fait !

Votre application est maintenant en production avec :
- ✅ HTTPS activé
- ✅ Services auto-redémarrables
- ✅ Base de données PostgreSQL
- ✅ Redis pour le cache
- ✅ Celery pour les tâches asynchrones
- ✅ Architecture multi-tenant