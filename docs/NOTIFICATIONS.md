# Système de Notifications - Cabinet Comptable

## Vue d'ensemble

Le système de notifications permet d'alerter automatiquement les utilisateurs sur :
- Les échéances proches (dans les 7 jours)
- Les documents manquants
- Les tâches en retard
- Les événements importants

## Architecture

### 1. Service d'Email (`app/services/email_service.py`)
- Gestion des templates HTML/texte avec Jinja2
- Support SMTP avec TLS/SSL
- Envoi asynchrone avec aiosmtplib

### 2. Service de Notifications (`app/services/notification_service.py`)
- Détection automatique des événements
- Création des alertes et notifications
- Prévention des doublons
- Gestion des notifications par cabinet (multi-tenant)

### 3. Tâches Celery (`app/tasks.py`)
- Exécution planifiée des vérifications
- Envoi asynchrone des emails
- Nettoyage automatique
- Mise à jour des statuts

### 4. API REST (`app/api/notifications.py`)
- Consultation des notifications
- Marquage comme lu
- Compteur de non-lues
- Test d'envoi d'email

## Configuration

### 1. Variables d'environnement (.env)

```bash
# Configuration SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=votre-email@gmail.com
SMTP_PASSWORD=mot-de-passe-application
SMTP_FROM_EMAIL=noreply@cabinet-comptable.fr
SMTP_FROM_NAME=Cabinet Comptable
SMTP_TLS=True
SMTP_SSL=False
```

### 2. Pour Gmail

1. Activez la vérification en 2 étapes
2. Créez un mot de passe d'application :
   - Allez dans les paramètres Google
   - Sécurité > Mots de passe d'applications
   - Créez un mot de passe pour "Mail"
3. Utilisez ce mot de passe dans `SMTP_PASSWORD`

### 3. Autres services SMTP

- **SendGrid**: smtp.sendgrid.net (port 587)
- **Mailgun**: smtp.mailgun.org (port 587)
- **AWS SES**: email-smtp.[region].amazonaws.com (port 587)
- **Outlook**: smtp-mail.outlook.com (port 587)

## Démarrage

### 1. Redis (prérequis)

```bash
# Installer Redis
sudo apt-get install redis-server

# Démarrer Redis
redis-server
```

### 2. Celery Worker

```bash
# Démarrer le worker
./scripts/start_celery_worker.sh

# Ou manuellement
celery -A app.core.celery_app worker --loglevel=info
```

### 3. Celery Beat (planificateur)

```bash
# Démarrer Beat
./scripts/start_celery_beat.sh

# Ou manuellement
celery -A app.core.celery_app beat --loglevel=info
```

## Utilisation

### 1. Test manuel

```bash
# Tester le système de notifications
venv/bin/python scripts/test_notifications.py

# Tester les tâches Celery
venv/bin/python scripts/test_celery_tasks.py
```

### 2. API Endpoints

```bash
# Obtenir les notifications
GET /api/v1/notifications

# Marquer comme lue
PUT /api/v1/notifications/{id}/read

# Nombre de non-lues
GET /api/v1/notifications/unread-count

# Test d'envoi
POST /api/v1/notifications/test-email
```

### 3. Planification automatique

Les tâches s'exécutent automatiquement :
- **9h00** : Vérification des notifications
- **14h00** : Vérification supplémentaire
- **Lundi 8h00** : Résumé hebdomadaire
- **Dimanche 2h00** : Nettoyage
- **Minuit** : Mise à jour des statuts

## Templates d'emails

Les templates sont dans `/templates/emails/` :

- `base.html/txt` : Template de base
- `echeance_proche.html/txt` : Échéances proches
- `documents_manquants.html/txt` : Documents requis
- `taches_retard.html/txt` : Tâches en retard
- `welcome.html/txt` : Email de bienvenue
- `test.html/txt` : Email de test

### Créer un nouveau template

1. Créez `mon_template.html` et `mon_template.txt`
2. Étendez le template de base :
   ```html
   {% extends "base.html" %}
   {% block content %}
   Votre contenu ici
   {% endblock %}
   ```
3. Utilisez dans le code :
   ```python
   await email_service.send_email(
       to_email="user@example.com",
       subject="Sujet",
       template_name="mon_template",
       template_data={"key": "value"}
   )
   ```

## Monitoring

### 1. Logs

```bash
# Logs du worker
tail -f celery_worker.log

# Logs de Beat
tail -f celery_beat.log
```

### 2. Commandes Celery

```bash
# Voir les tâches actives
celery -A app.core.celery_app inspect active

# Voir les tâches planifiées
celery -A app.core.celery_app inspect scheduled

# Statistiques
celery -A app.core.celery_app inspect stats

# Purger les tâches
celery -A app.core.celery_app purge
```

### 3. Interface Flower (optionnel)

```bash
# Installer Flower
pip install flower

# Démarrer Flower
celery -A app.core.celery_app flower

# Accéder à http://localhost:5555
```

## Dépannage

### Email non envoyé

1. Vérifiez la configuration SMTP dans `.env`
2. Testez avec : `venv/bin/python scripts/test_notifications.py`
3. Vérifiez les logs du worker Celery
4. Pour Gmail, vérifiez les "Applications moins sécurisées" ou utilisez un mot de passe d'application

### Tâches non exécutées

1. Vérifiez que Redis est démarré : `redis-cli ping`
2. Vérifiez que le worker est actif : `celery inspect active`
3. Vérifiez que Beat est démarré pour les tâches planifiées
4. Consultez les logs pour les erreurs

### Performance

- Utilisez plusieurs workers : `--concurrency=4`
- Séparez les queues : notifications, emails, maintenance
- Limitez les tâches par worker : `--max-tasks-per-child=1000`
- Surveillez Redis : `redis-cli info`

## Intégration Frontend

### 1. Websocket pour notifications temps réel

```javascript
// Connexion websocket
const ws = new WebSocket('ws://localhost:8000/ws/notifications');

ws.onmessage = (event) => {
  const notification = JSON.parse(event.data);
  // Afficher la notification
};
```

### 2. API pour récupérer les notifications

```javascript
// Obtenir les notifications
const response = await fetch('/api/v1/notifications', {
  headers: { 'Authorization': `Bearer ${token}` }
});

// Marquer comme lue
await fetch(`/api/v1/notifications/${id}/read`, {
  method: 'PUT',
  headers: { 'Authorization': `Bearer ${token}` }
});
```

### 3. Badge de notifications

```javascript
// Obtenir le nombre de non-lues
const response = await fetch('/api/v1/notifications/unread-count', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const { unread_count } = await response.json();
```