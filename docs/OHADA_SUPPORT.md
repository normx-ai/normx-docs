# Support OHADA - Cabinet Comptable

## Vue d'ensemble

L'application Cabinet Comptable supporte les 17 pays membres de l'OHADA (Organisation pour l'Harmonisation en Afrique du Droit des Affaires) ainsi que la France.

## Pays Supportés

### Zone CEMAC (Franc CFA XAF)
1. 🇨🇲 **Cameroun** (CM)
2. 🇬🇦 **Gabon** (GA)
3. 🇨🇬 **Congo-Brazzaville** (CG)
4. 🇹🇩 **Tchad** (TD)
5. 🇨🇫 **République Centrafricaine** (CF)
6. 🇬🇶 **Guinée Équatoriale** (GQ)

### Zone UEMOA (Franc CFA XOF)
7. 🇸🇳 **Sénégal** (SN)
8. 🇨🇮 **Côte d'Ivoire** (CI)
9. 🇧🇫 **Burkina Faso** (BF)
10. 🇲🇱 **Mali** (ML)
11. 🇹🇬 **Togo** (TG)
12. 🇧🇯 **Bénin** (BJ)
13. 🇳🇪 **Niger** (NE)
14. 🇬🇼 **Guinée-Bissau** (GW)

### Autres pays OHADA
15. 🇰🇲 **Comores** (KM) - Franc comorien (KMF)
16. 🇬🇳 **Guinée** (GN) - Franc guinéen (GNF)
17. 🇨🇩 **RD Congo** (CD) - Franc congolais (CDF)

### Pays supplémentaire
18. 🇫🇷 **France** (FR) - Euro (EUR)

## Fonctionnalités par Pays

### 1. Validation des numéros de téléphone

Chaque pays a son format spécifique :

| Pays | Format | Exemple |
|------|--------|---------|
| Cameroun | +237 6/2 XX XX XX XX | +237 691 234 567 |
| Sénégal | +221 7/3 XX XX XX XX | +221 771 234 567 |
| Côte d'Ivoire | +225 XX XX XX XX XX | +225 07 123 456 78 |
| France | +33 X XX XX XX XX | +33 6 12 34 56 78 |

### 2. Identifiants d'entreprise

Chaque pays utilise un identifiant différent :

| Pays | Identifiant | Longueur | Format |
|------|-------------|----------|---------|
| France | SIRET | 14 chiffres | Validation Luhn |
| Cameroun | N° Contribuable | 14 caractères | M/P + 13 chiffres |
| Sénégal | NINEA | 9 chiffres | Numérique |
| Côte d'Ivoire | CC | 16 caractères | CI + 14 caractères |
| Gabon | NIF | 13 caractères | Alphanumérique |
| Burkina Faso | IFU | 12 chiffres | Numérique |
| Mali | NIF | 9 chiffres | Numérique |
| Togo | NIF | 13 caractères | Alphanumérique |
| Bénin | IFU | 13 caractères | Alphanumérique |
| Congo | NIU | 14 caractères | Alphanumérique |
| Tchad | NIF | 13 caractères | Alphanumérique |
| RCA | NIF | 12 caractères | Alphanumérique |
| Guinée Éq. | NIF | 12 caractères | Alphanumérique |
| Niger | NIF | 12 caractères | Alphanumérique |
| Guinée-Bissau | NIF | 10 caractères | Alphanumérique |
| Comores | NIF | 10 caractères | Alphanumérique |
| Guinée | NIF | 9 caractères | Numérique |
| RD Congo | NIF | 14 caractères | Numérique |

### 3. Formats IBAN

Les IBAN varient selon les pays :

| Pays | Longueur | Préfixe | Exemple |
|------|----------|---------|---------|
| France | 27 | FR | FR14 2004 1010 0505 0001 3M02 606 |
| Zone CEMAC | 27 | CM/GA/CG/TD/CF/GQ | CM21 1001 1001 2345 6789 0123 4567 |
| Zone UEMOA | 28 | SN/CI/BF/ML/TG/BJ/NE | SN12 K001 0015 2000 0256 9000 7542 |
| Guinée-Bissau | 25 | GW | GW00 1234 5678 9012 3456 789 |
| Comores | 27 | KM | KM46 0005 0010 0101 2345 6789 012 |
| Guinée | 27 | GN | GN00 1234 5678 9012 3456 7890 123 |
| RD Congo | 27 | CD | CD00 1234 5678 9012 3456 7890 123 |

## Configuration dans l'Application

### 1. Configuration du Cabinet

Lors de la création d'un cabinet, vous pouvez spécifier :
- **Code pays** : Le code ISO à 2 lettres (ex: CM pour Cameroun)
- **Langue** : La variante locale du français (ex: fr-CM)
- **Fuseau horaire** : Le fuseau horaire approprié
- **Devise** : Automatiquement définie selon le pays

### 2. API Endpoints

```bash
# Obtenir tous les pays supportés
GET /api/v1/cabinet-settings/supported-countries

# Obtenir les détails d'un pays
GET /api/v1/cabinet-settings/country/{country_code}

# Mettre à jour les paramètres du cabinet
PUT /api/v1/cabinet-settings/settings
{
  "pays_code": "CM",
  "langue": "fr-CM",
  "fuseau_horaire": "Africa/Douala"
}
```

### 3. Utilisation dans le Code

```python
from app.core.validators import (
    validate_phone,
    validate_company_id,
    validate_iban,
    format_phone_number,
    get_country_info
)

# Validation selon le pays du cabinet
country_code = cabinet.pays_code  # ex: "CM"

# Valider un téléphone
if validate_phone("237691234567", country_code):
    formatted = format_phone_number("237691234567", country_code)
    # Résultat: "+237 69 12 34 567"

# Valider un identifiant d'entreprise
if validate_company_id("M1234567890123", country_code):
    # Numéro de contribuable camerounais valide

# Obtenir les informations du pays
info = get_country_info(country_code)
print(f"Devise: {info['currency']}")  # XAF
print(f"Format téléphone: {info['phone_format']}")
```

## Fuseaux Horaires

### Répartition par fuseau

- **Africa/Douala** : Cameroun, Gabon, Tchad, RCA, Guinée Équatoriale, Congo
- **Africa/Dakar** : Sénégal, Mali, Guinée-Bissau
- **Africa/Abidjan** : Côte d'Ivoire, Burkina Faso, Togo, Bénin, Niger
- **Africa/Conakry** : Guinée
- **Africa/Kinshasa** : RD Congo (ouest)
- **Africa/Lubumbashi** : RD Congo (est)
- **Indian/Comoro** : Comores
- **Europe/Paris** : France

## Particularités Comptables OHADA

### 1. Plan comptable SYSCOHADA

L'application supporte le plan comptable SYSCOHADA révisé, commun à tous les pays OHADA :
- Classes 1-8 standardisées
- Comptes divisionnaires adaptés
- États financiers conformes

### 2. Déclarations fiscales

Chaque pays a ses spécificités :
- **Cameroun** : DSF mensuelle, déclaration TVA
- **Sénégal** : NINEA obligatoire pour toute déclaration
- **Côte d'Ivoire** : Télédéclaration via DGI
- **Gabon** : e-Tax pour les déclarations

### 3. Formats de dates

Tous les pays OHADA utilisent le format DD/MM/YYYY, facilitant l'uniformité.

## Test et Validation

### Script de test

```bash
# Tester les validations internationales
venv/bin/python scripts/demo_international_validators.py
```

### Validation en production

1. Toujours valider selon le pays du cabinet
2. Afficher des messages d'erreur appropriés avec le format attendu
3. Formater automatiquement les données lors de l'affichage

## Évolutions Futures

- Support des langues locales (Wolof, Lingala, etc.)
- Intégration avec les systèmes fiscaux nationaux
- Templates de documents adaptés par pays
- Calculs fiscaux spécifiques par juridiction

## Support et Documentation

Pour toute question sur l'implémentation OHADA :
- Consultez la documentation API
- Référez-vous aux validateurs dans `app/core/validators.py`
- Testez avec le script de démonstration