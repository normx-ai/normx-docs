# API d'Inscription avec Support Multi-Pays

## Vue d'ensemble

L'API d'inscription (`POST /api/v1/auth/register`) a été étendue pour supporter les 17 pays OHADA + la France. Elle gère automatiquement :
- La création du cabinet lors de la première inscription
- La validation des données selon le pays choisi
- La configuration automatique des paramètres localisés

## Endpoints

### 1. Obtenir la liste des pays

```http
GET /api/v1/auth/countries
```

Retourne la liste des pays disponibles pour l'inscription.

**Réponse :**
```json
[
  {
    "code": "FR",
    "name": "France",
    "currency": "EUR",
    "company_id_label": "SIRET",
    "phone_placeholder": "0123456789",
    "phone_format": "0123456789 ou +33123456789"
  },
  {
    "code": "CM",
    "name": "Cameroun",
    "currency": "XAF",
    "company_id_label": "Numéro du Contribuable",
    "phone_placeholder": "237691234567",
    "phone_format": "237691234567 ou +237691234567"
  },
  // ... autres pays
]
```

### 2. S'inscrire avec création du cabinet

```http
POST /api/v1/auth/register
```

**Corps de la requête :**
```json
{
  // Informations utilisateur (obligatoires)
  "username": "admin",
  "email": "admin@exemple.com",
  "password": "MotDePasse123!",
  "full_name": "Jean Dupont",
  
  // Informations cabinet
  "cabinet_name": "Cabinet Dupont & Associés",
  "pays_code": "CM",  // Code ISO du pays
  
  // Optionnel selon le pays
  "siret": "M1234567890123",  // Numéro du contribuable pour le Cameroun
  "telephone_cabinet": "237691234567",
  "adresse": "Boulevard de la Liberté",
  "code_postal": "",  // Pas utilisé au Cameroun
  "ville": "Douala",
  
  // role est automatiquement "admin" pour le premier utilisateur
  "role": "collaborateur"  // sera ignoré et remplacé par "admin"
}
```

**Réponse en cas de succès :**
```json
{
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@exemple.com",
    "full_name": "Jean Dupont",
    "role": "admin",
    "cabinet_id": 1,
    "cabinet_name": "Cabinet Dupont & Associés"
  },
  "cabinet": {
    "id": 1,
    "nom": "Cabinet Dupont & Associés",
    "pays_code": "CM",
    "devise": "XAF"
  },
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "message": "Bienvenue dans Cabinet Dupont & Associés !"
}
```

## Validations par pays

### France (FR)
- **SIRET** : Obligatoire, 14 chiffres, validation Luhn
- **Code postal** : Obligatoire, 5 chiffres
- **Téléphone** : Format 0XXXXXXXXX ou +33XXXXXXXXX

### Cameroun (CM)
- **Numéro du Contribuable** : Format M ou P + 13 chiffres
- **Téléphone** : Format 237[26]XXXXXXXX
- **Code postal** : Non requis

### Sénégal (SN)
- **NINEA** : 9 chiffres
- **Téléphone** : Format 221[37]XXXXXXXX
- **Code postal** : Non requis

## Exemples d'utilisation

### 1. Inscription depuis la France

```javascript
const registerFrance = async () => {
  const response = await fetch('/api/v1/auth/register', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      username: 'cabinet_paris',
      email: 'contact@cabinet-paris.fr',
      password: 'SecurePass123!',
      full_name: 'Marie Martin',
      cabinet_name: 'Cabinet Martin & Associés',
      pays_code: 'FR',
      siret: '80314979300020',
      telephone_cabinet: '0142861234',
      adresse: '15 rue de la Paix',
      code_postal: '75002',
      ville: 'Paris'
    })
  });
  
  const data = await response.json();
  
  // Stocker le token
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('cabinet_id', data.cabinet.id);
};
```

### 2. Inscription depuis le Cameroun

```javascript
const registerCameroun = async () => {
  const response = await fetch('/api/v1/auth/register', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      username: 'cabinet_douala',
      email: 'contact@cabinet-douala.cm',
      password: 'SecurePass123!',
      full_name: 'Paul Mbarga',
      cabinet_name: 'Cabinet Mbarga & Partners',
      pays_code: 'CM',
      siret: 'M1234567890123',
      telephone_cabinet: '237691234567',
      adresse: 'Boulevard de la Liberté',
      ville: 'Douala'
    })
  });
  
  const data = await response.json();
  console.log('Cabinet créé avec devise:', data.cabinet.devise); // XAF
};
```

### 3. Vérifier la disponibilité avant inscription

```javascript
// Vérifier si le nom d'utilisateur est disponible
const checkUsername = async (username) => {
  const response = await fetch('/api/v1/cabinet-settings/check-availability', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      field: 'username',
      value: username
    })
  });
  
  const data = await response.json();
  return data.available;
};
```

## Erreurs possibles

### 400 - Bad Request
```json
{
  "detail": "Code pays non supporté: XX"
}
```

```json
{
  "detail": "Format de téléphone invalide. Format attendu: 237612345678 ou +237612345678"
}
```

```json
{
  "detail": "Numéro du Contribuable invalide"
}
```

```json
{
  "detail": "Le mot de passe doit contenir au moins une majuscule"
}
```

### 409 - Conflict
```json
{
  "detail": "Ce nom d'utilisateur existe déjà"
}
```

## Configuration automatique

Lors de la création du cabinet, les paramètres suivants sont automatiquement configurés selon le pays :

| Paramètre | Exemple Cameroun | Exemple France |
|-----------|------------------|----------------|
| Langue | fr-CM | fr-FR |
| Fuseau horaire | Africa/Douala | Europe/Paris |
| Devise | XAF | EUR |
| Format date | DD/MM/YYYY | DD/MM/YYYY |
| Plan | trial | trial |
| Limite utilisateurs | 5 | 5 |
| Limite clients | 50 | 50 |

## Flux d'inscription recommandé

1. **Charger les pays** : `GET /api/v1/auth/countries`
2. **Afficher le formulaire** avec les champs adaptés au pays
3. **Valider côté client** selon les règles du pays
4. **Soumettre l'inscription** : `POST /api/v1/auth/register`
5. **Stocker le token** et rediriger vers le dashboard

## Notes importantes

- Le premier utilisateur devient automatiquement administrateur
- Le cabinet est créé uniquement lors de la première inscription
- Les utilisateurs suivants rejoignent le cabinet existant
- La validation est stricte selon le pays choisi
- Le SIREN est extrait automatiquement du SIRET pour la France