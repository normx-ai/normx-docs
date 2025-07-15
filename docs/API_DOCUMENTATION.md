# 📚 Documentation API - NormX Docs v2.0

## Vue d'ensemble

L'API NormX Docs v2.0 est une API RESTful sécurisée pour la gestion des dossiers clients comptables. Cette version intègre des améliorations majeures en termes de sécurité, performance et fonctionnalités.

### 🔒 Nouvelles fonctionnalités de sécurité

- **Authentification à deux facteurs (2FA)**
- **Refresh tokens** pour une meilleure gestion des sessions
- **Validation stricte des uploads** de fichiers
- **Headers de sécurité** renforcés
- **Logs structurés** avec rotation automatique
- **Rate limiting** pour prévenir les abus

### ⚡ Améliorations de performance

- **Cache Redis** pour les données fréquemment consultées
- **Pagination** sur tous les endpoints de liste
- **Requêtes optimisées** (eager loading)

## Base URL

```
Production: https://api.votre-domaine.com
Development: http://localhost:8000
```

## Authentification

L'API utilise JWT (JSON Web Tokens) avec un système de refresh tokens.

### Login

```http
POST /api/v1/auth/token
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=SecurePassword123!
```

**Réponse sans 2FA:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "refresh_token": "Xs2mYPqR3...",
  "expires_in": 86400
}
```

**Réponse avec 2FA activé:**
```json
{
  "requires_2fa": true,
  "session_token": "temp_session_token",
  "message": "Veuillez entrer votre code d'authentification"
}
```

### Vérification 2FA

```http
POST /api/v1/auth/verify-2fa
Content-Type: application/json

{
  "session_token": "temp_session_token",
  "code": "123456"
}
```

### Refresh Token

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "your_refresh_token"
}
```

### Headers requis

Pour toutes les requêtes authentifiées :

```http
Authorization: Bearer <access_token>
```

## Endpoints

### 🏢 Cabinets

#### Configuration du cabinet

```http
GET /api/v1/cabinet-settings
PUT /api/v1/cabinet-settings
```

### 👥 Utilisateurs

#### Liste des utilisateurs

```http
GET /api/v1/users
```

**Paramètres de requête:**
- `role`: Filtrer par rôle (admin, manager, collaborateur)
- `active`: Filtrer par statut actif (true/false)

#### Créer un utilisateur

```http
POST /api/v1/users
Content-Type: application/json

{
  "username": "john.doe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "role": "collaborateur"
}
```

### 📁 Dossiers

#### Liste des dossiers (avec pagination)

```http
GET /api/v1/dossiers/?limit=20&offset=0
```

**Paramètres:**
- `limit`: Nombre maximum de résultats (1-500, défaut: 100)
- `offset`: Décalage pour la pagination (défaut: 0)
- `status`: Filtrer par statut
- `responsable_id`: Filtrer par responsable
- `urgent`: Dossiers urgents uniquement (true/false)

#### Créer un dossier

```http
POST /api/v1/dossiers
Content-Type: application/json

{
  "nom": "Dossier Client 2025",
  "nom_client": "Entreprise ABC",
  "type_dossier": "COMPTABILITE",
  "date_debut": "2025-01-01",
  "date_echeance": "2025-01-31",
  "responsable_id": 1
}
```

### 📄 Documents

#### Upload de documents (sécurisé)

```http
POST /api/v1/dossiers/{dossier_id}/documents/upload
Content-Type: multipart/form-data

files: (binary)
type: FACTURE_ACHAT
echeance_id: 123
```

**Validation appliquée:**
- Extensions autorisées: .pdf, .doc, .docx, .xls, .xlsx, .png, .jpg, .jpeg
- Taille maximale: 10 MB par fichier
- Vérification du contenu (MIME type)
- Détection de signatures dangereuses
- Génération de nom sécurisé

### 🔐 Authentification à deux facteurs

#### Activer 2FA - Étape 1: Configuration

```http
POST /api/v1/2fa/setup
```

**Réponse:**
```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code": "data:image/png;base64,iVBORw0KG...",
  "backup_codes": [
    "123456",
    "234567",
    "345678",
    "456789",
    "567890",
    "678901",
    "789012",
    "890123"
  ]
}
```

#### Activer 2FA - Étape 2: Validation

```http
POST /api/v1/2fa/enable
Content-Type: application/json

{
  "token": "123456"
}
```

#### Désactiver 2FA

```http
POST /api/v1/2fa/disable
Content-Type: application/json

{
  "token": "123456"
}
```

### 📊 Dashboard & Statistiques

#### Statistiques du dashboard (avec cache)

```http
GET /api/v1/dashboard/stats?period=month
```

**Cache:** 5 minutes

### 🔔 Notifications

#### WebSocket pour notifications temps réel

```javascript
const ws = new WebSocket('wss://api.votre-domaine.com/api/v1/ws');

ws.onmessage = (event) => {
  const notification = JSON.parse(event.data);
  console.log('Nouvelle notification:', notification);
};
```

## Codes d'erreur

| Code | Description |
|------|-------------|
| 400 | Bad Request - Données invalides |
| 401 | Unauthorized - Token invalide ou expiré |
| 403 | Forbidden - Permissions insuffisantes |
| 404 | Not Found - Ressource non trouvée |
| 413 | Payload Too Large - Fichier trop volumineux |
| 422 | Unprocessable Entity - Erreur de validation |
| 429 | Too Many Requests - Rate limit dépassé |
| 500 | Internal Server Error |

## Rate Limiting

- **Par minute:** 60 requêtes
- **Par heure:** 1000 requêtes

Headers de réponse:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1673612400
```

## Sécurité

### Headers de sécurité appliqués

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'...
Strict-Transport-Security: max-age=31536000
```

### Validation des données

- Validation Pydantic sur toutes les entrées
- Sanitisation des chaînes de caractères
- Validation des formats (email, téléphone, SIRET)
- Limite de taille sur les payloads

## Exemples complets

### Workflow complet d'authentification avec 2FA

```python
import requests
import pyotp

# 1. Login initial
login_response = requests.post(
    "https://api.votre-domaine.com/api/v1/auth/token",
    data={
        "username": "user@example.com",
        "password": "password"
    }
)

if login_response.json().get("requires_2fa"):
    # 2. Si 2FA est activé
    session_token = login_response.json()["session_token"]
    
    # Générer le code TOTP
    totp = pyotp.TOTP("votre_secret_2fa")
    code = totp.now()
    
    # 3. Vérifier le code 2FA
    auth_response = requests.post(
        "https://api.votre-domaine.com/api/v1/auth/verify-2fa",
        json={
            "session_token": session_token,
            "code": code
        }
    )
    
    access_token = auth_response.json()["access_token"]
    refresh_token = auth_response.json()["refresh_token"]
else:
    # Sans 2FA
    access_token = login_response.json()["access_token"]
    refresh_token = login_response.json()["refresh_token"]

# 4. Utiliser l'API
headers = {"Authorization": f"Bearer {access_token}"}
dossiers = requests.get(
    "https://api.votre-domaine.com/api/v1/dossiers/",
    headers=headers
)
```

### Upload sécurisé de fichier

```python
# Upload d'un document
with open("facture.pdf", "rb") as f:
    response = requests.post(
        f"https://api.votre-domaine.com/api/v1/dossiers/{dossier_id}/documents/upload",
        headers=headers,
        files={"files": ("facture.pdf", f, "application/pdf")},
        data={
            "type": "FACTURE_ACHAT",
            "echeance_id": echeance_id
        }
    )
```

## Migration depuis v1.0

### Changements breaking

1. **Authentification:** Le login retourne maintenant `refresh_token`
2. **2FA:** Peut nécessiter une étape supplémentaire après login
3. **Pagination:** Limite par défaut de 100 résultats
4. **Headers:** CORS plus restrictif

### Guide de migration

1. Mettre à jour la gestion du login pour supporter 2FA
2. Implémenter la logique de refresh token
3. Ajouter la gestion de la pagination
4. Vérifier la compatibilité CORS

## Support

Pour toute question sur l'API :
- Documentation interactive : https://api.votre-domaine.com/docs
- Email : support@votre-domaine.com