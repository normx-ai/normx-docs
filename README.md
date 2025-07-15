# NormX Docs - Suivi Intelligent de Dossiers

## 📋 Description

NormX Docs - Application de suivi intelligent des dossiers clients pour cabinet comptable avec système d'alertes automatisées et génération de points quotidiens.

## 🏗️ Architecture

```
Frontend (React) → API REST (FastAPI) → PostgreSQL
                                     ↓
                            Moteur IA (Python + ML)
                                     ↓
                        Système d'alertes (Redis + Celery)
```

## 🚀 Installation

### Prérequis
- Python 3.12+
- PostgreSQL 14+
- Redis 6+

### Configuration

1. **Cloner le projet**
```bash
git clone [votre-repo]
cd gd-ia-comptable
```

2. **Créer l'environnement virtuel**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

4. **Configurer la base de données**
```bash
# Créer la base PostgreSQL
sudo -u postgres psql < scripts/create_db.sql

# Copier et configurer le fichier .env
cp .env.example .env
# Éditer .env avec vos paramètres
```

5. **Lancer les migrations**
```bash
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

## 🖥️ Utilisation

### Démarrer tous les services
```bash
./scripts/start_services.sh
```

Ou manuellement :

```bash
# Terminal 1 - API
uvicorn app.main:app --reload

# Terminal 2 - Worker Celery
celery -A app.core.celery_app worker --loglevel=info

# Terminal 3 - Scheduler Celery Beat
celery -A app.core.celery_app beat --loglevel=info
```

### Accès
- API : http://localhost:8000
- Documentation : http://localhost:8000/docs

## 📁 Structure du projet

```
gd-ia-comptable/
├── app/
│   ├── api/              # Endpoints API
│   ├── core/             # Configuration, sécurité
│   ├── models/           # Modèles SQLAlchemy
│   ├── services/         # Logique métier
│   ├── workers/          # Tâches Celery
│   └── ml/               # Modèles IA
├── tests/                # Tests unitaires
├── alembic/              # Migrations DB
├── scripts/              # Scripts utilitaires
└── docs/                 # Documentation
```

## 🔧 Fonctionnalités principales

- **Gestion des dossiers** : Création, suivi, mise à jour
- **Alertes automatiques** : Retards, deadlines, inactivité
- **Points quotidiens** : Synthèse automatique à 8h30
- **Notifications** : In-app et email
- **Traitement IA** : OCR et extraction de données

## 🧪 Tests

```bash
pytest tests/
```

## 📝 Licence

[Votre licence]