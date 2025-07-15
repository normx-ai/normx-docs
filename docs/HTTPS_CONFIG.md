# Configuration HTTPS pour Production

## Vue d'ensemble

Ce guide explique comment configurer HTTPS pour l'application Cabinet Comptable en production avec Nginx et Let's Encrypt.

## Prérequis

- Serveur Linux (Ubuntu/Debian recommandé)
- Nom de domaine pointant vers votre serveur
- Nginx installé
- Certbot installé pour Let's Encrypt

## Installation des prérequis

```bash
# Mettre à jour le système
sudo apt update && sudo apt upgrade -y

# Installer Nginx
sudo apt install nginx -y

# Installer Certbot et le plugin Nginx
sudo apt install certbot python3-certbot-nginx -y
```

## Configuration Nginx

### 1. Créer le fichier de configuration

```bash
sudo nano /etc/nginx/sites-available/cabinet-comptable
```

### 2. Configuration de base (HTTP)

```nginx
server {
    listen 80;
    server_name votre-domaine.com www.votre-domaine.com;

    # Logs
    access_log /var/log/nginx/cabinet-comptable.access.log;
    error_log /var/log/nginx/cabinet-comptable.error.log;

    # Taille maximale des uploads (10MB)
    client_max_body_size 10M;

    # Headers de sécurité
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # Proxy vers l'API FastAPI
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeout pour les longues requêtes
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
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
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Frontend React
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### 3. Activer le site

```bash
# Créer un lien symbolique
sudo ln -s /etc/nginx/sites-available/cabinet-comptable /etc/nginx/sites-enabled/

# Tester la configuration
sudo nginx -t

# Recharger Nginx
sudo systemctl reload nginx
```

## Configuration HTTPS avec Let's Encrypt

### 1. Obtenir le certificat SSL

```bash
sudo certbot --nginx -d votre-domaine.com -d www.votre-domaine.com
```

Suivez les instructions :
- Entrez votre email
- Acceptez les conditions
- Choisissez de rediriger HTTP vers HTTPS (recommandé)

### 2. Configuration HTTPS complète

Après Certbot, votre configuration sera automatiquement mise à jour. Voici la configuration finale optimisée :

```nginx
# Redirection HTTP vers HTTPS
server {
    listen 80;
    server_name votre-domaine.com www.votre-domaine.com;
    return 301 https://$server_name$request_uri;
}

# Configuration HTTPS
server {
    listen 443 ssl http2;
    server_name votre-domaine.com www.votre-domaine.com;

    # Certificats SSL (gérés par Certbot)
    ssl_certificate /etc/letsencrypt/live/votre-domaine.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/votre-domaine.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Configuration SSL moderne
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';

    # HSTS (HTTP Strict Transport Security)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Headers de sécurité
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' https:; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';" always;

    # Logs
    access_log /var/log/nginx/cabinet-comptable.access.log;
    error_log /var/log/nginx/cabinet-comptable.error.log;

    # Taille maximale des uploads
    client_max_body_size 10M;

    # Compression Gzip
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # Cache pour les assets statiques
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|pdf)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # API Backend
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Sécurité supplémentaire
        proxy_set_header X-Forwarded-Host $server_name;
        proxy_redirect off;
        
        # Timeouts
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout plus long pour WebSocket
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

## Renouvellement automatique

Let's Encrypt configure automatiquement le renouvellement. Vérifiez avec :

```bash
# Tester le renouvellement
sudo certbot renew --dry-run

# Voir le timer systemd
systemctl list-timers | grep certbot
```

## Configuration de l'application

### 1. Mettre à jour .env pour la production

```bash
# .env.production
ENV=production
DEBUG=False

# Domaine pour CORS
CORS_ORIGINS=["https://votre-domaine.com","https://www.votre-domaine.com"]

# Forcer HTTPS dans les cookies
SECURE_COOKIES=True
SAMESITE_COOKIES=Strict
```

### 2. Mettre à jour settings.py

```python
# app/core/config.py
class Settings(BaseSettings):
    # ... autres configs ...
    
    # Sécurité HTTPS
    SECURE_COOKIES: bool = Field(default=False)
    SAMESITE_COOKIES: str = Field(default="Lax")
    
    @property
    def cookie_secure(self) -> bool:
        return self.SECURE_COOKIES or self.ENV == "production"
```

## Tests de sécurité

### 1. Test SSL Labs

Testez votre configuration SSL sur : https://www.ssllabs.com/ssltest/

Vous devriez obtenir une note A ou A+.

### 2. Test des headers de sécurité

Testez sur : https://securityheaders.com/

### 3. Test local avec curl

```bash
# Test HTTPS
curl -I https://votre-domaine.com

# Test redirection HTTP -> HTTPS
curl -I http://votre-domaine.com

# Test WebSocket
wscat -c wss://votre-domaine.com/ws/notifications
```

## Monitoring

### 1. Logs Nginx

```bash
# Logs d'accès
sudo tail -f /var/log/nginx/cabinet-comptable.access.log

# Logs d'erreurs
sudo tail -f /var/log/nginx/cabinet-comptable.error.log
```

### 2. Status Nginx

```bash
# Status du service
sudo systemctl status nginx

# Statistiques
sudo nginx -V
```

## Firewall

Configurez le firewall pour autoriser HTTPS :

```bash
# UFW (Ubuntu)
sudo ufw allow 'Nginx Full'
sudo ufw delete allow 'Nginx HTTP'
sudo ufw status

# Ou avec iptables
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
```

## Optimisations supplémentaires

### 1. HTTP/2 Push

```nginx
location / {
    http2_push /static/css/main.css;
    http2_push /static/js/main.js;
    # ...
}
```

### 2. Cache Nginx

```nginx
# Dans http block
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=100m inactive=60m;

# Dans location /api
proxy_cache api_cache;
proxy_cache_valid 200 5m;
proxy_cache_valid 404 1m;
proxy_cache_bypass $http_authorization;
```

### 3. Rate Limiting Nginx

```nginx
# Dans http block
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

# Dans location /api
limit_req zone=api_limit burst=20 nodelay;
```

## Dépannage

### Problème : Erreur 502 Bad Gateway

1. Vérifiez que l'application est lancée
2. Vérifiez les logs : `sudo tail -f /var/log/nginx/error.log`
3. Testez l'accès direct : `curl http://localhost:8000/api/v1/health`

### Problème : WebSocket ne fonctionne pas

1. Vérifiez les headers Upgrade dans Nginx
2. Testez sans proxy : `wscat -c ws://localhost:8000/ws/notifications`
3. Vérifiez les logs de l'application

### Problème : Certificat Let's Encrypt échoue

1. Vérifiez que le domaine pointe vers le serveur
2. Vérifiez que le port 80 est accessible
3. Testez avec : `sudo certbot certonly --nginx --dry-run -d votre-domaine.com`

## Checklist de sécurité

- [ ] HTTPS activé et HTTP redirigé
- [ ] Headers de sécurité configurés
- [ ] HSTS activé
- [ ] Certificats SSL valides et auto-renouvelés
- [ ] Rate limiting configuré (Nginx + application)
- [ ] Logs activés et surveillés
- [ ] Firewall configuré
- [ ] Compression Gzip activée
- [ ] Cache configuré pour les assets statiques
- [ ] Mises à jour de sécurité appliquées