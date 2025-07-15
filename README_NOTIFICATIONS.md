# Système de Notifications et Rappels - NormX Docs

## Vue d'ensemble

Le système de notifications en temps réel et de rappels automatiques utilise WebSockets pour les notifications instantanées et Celery pour les tâches planifiées.

## Architecture

### 1. WebSocket pour les notifications en temps réel
- **Endpoint** : `ws://localhost:8000/api/v1/ws/{token}`
- **Authentification** : Token JWT passé dans l'URL
- **Types de notifications** :
  - `dossier_update` : Mise à jour d'un dossier
  - `new_alert` : Nouvelle alerte urgente
  - `deadline_reminder` : Rappel d'échéance
  - `daily_report` : Rapport quotidien

### 2. Celery pour les rappels automatiques
- **Broker** : Redis
- **Tâches planifiées** :
  - Vérification des échéances (8h du matin)
  - Vérification des dossiers urgents (toutes les heures)
  - Rapport quotidien (18h)
  - Vérification des retards (toutes les 30 minutes)

## Installation et Configuration

### 1. Installation des dépendances

```bash
# Backend
cd /home/chris/gd-ia-comptable
source venv/bin/activate
pip install websockets celery redis python-socketio[asyncio_client]

# Frontend - déjà inclus dans package.json
```

### 2. Démarrage de Redis

```bash
# Si Redis n'est pas installé
sudo apt-get install redis-server

# Démarrer Redis
redis-server
```

### 3. Démarrage de Celery

```bash
# Dans un terminal séparé
cd /home/chris/gd-ia-comptable
./start_celery.sh

# Ou manuellement :
# Worker
celery -A app.core.celery_config worker --loglevel=info

# Beat (scheduler)
celery -A app.core.celery_config beat --loglevel=info
```

## Utilisation

### Frontend

Le WebSocket se connecte automatiquement lors de la connexion de l'utilisateur. Les notifications apparaissent :
1. Dans la cloche de notification en haut à droite
2. Comme notifications du navigateur (si autorisées)

### Backend

Pour envoyer une notification depuis le code :

```python
from app.tasks.notifications import notify_dossier_created

# Après création d'un dossier
notify_dossier_created.delay(user_id, dossier_data)
```

## Types de rappels automatiques

### 1. Rappels d'échéance
- **J-7** : Rappel une semaine avant l'échéance
- **J-1** : Rappel la veille de l'échéance
- **Jour J** : Notification le jour de l'échéance

### 2. Alertes de retard
- **Nouveau retard** : Dès qu'un dossier dépasse sa date d'échéance
- **Retard critique** : Après 3 jours de retard

### 3. Dossiers urgents
- Vérification toutes les heures
- Notification si un dossier est marqué comme urgent

### 4. Rapport quotidien
- Envoyé à 18h
- Résumé : dossiers en retard, à traiter aujourd'hui, urgents

## Configuration des tâches planifiées

Modifier `app/core/celery_config.py` pour ajuster les horaires :

```python
celery_app.conf.beat_schedule = {
    "check-deadlines-morning": {
        "task": "app.tasks.reminders.check_deadlines",
        "schedule": crontab(hour=8, minute=0),  # Modifier l'heure ici
    },
    # ...
}
```

## Monitoring

### Vérifier l'état de Celery

```bash
# Voir les workers actifs
celery -A app.core.celery_config status

# Voir les tâches en cours
celery -A app.core.celery_config inspect active

# Voir les tâches planifiées
celery -A app.core.celery_config inspect scheduled
```

### Logs

- **API WebSocket** : Dans les logs FastAPI
- **Celery Worker** : Dans le terminal du worker
- **Celery Beat** : Dans le terminal du beat

## Troubleshooting

### WebSocket ne se connecte pas
1. Vérifier que l'API est démarrée
2. Vérifier le token JWT dans localStorage
3. Vérifier la console du navigateur

### Notifications non reçues
1. Vérifier que Redis est démarré
2. Vérifier que Celery Worker est actif
3. Vérifier les logs Celery pour les erreurs

### Rappels non envoyés
1. Vérifier que Celery Beat est démarré
2. Vérifier la configuration des tâches
3. Vérifier les fuseaux horaires