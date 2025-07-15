# Identifiants d'Entreprise OHADA

## Vue d'ensemble

Dans l'espace OHADA, les entreprises utilisent principalement deux types d'identifiants :
- **RCCM** : Registre du Commerce et du Crédit Mobilier
- **NUI** : Numéro Unique d'Identification (dans certains pays)

## Format RCCM Standard OHADA

Le format RCCM suit généralement cette structure :
```
[PAYS]-[VILLE]-[ANNEE]-[TYPE]-[NUMERO]
```

- **PAYS** : Code ISO du pays (2 lettres)
- **VILLE** : Code de la ville d'enregistrement (3 lettres)
- **ANNEE** : Année d'enregistrement (4 chiffres)
- **TYPE** : Type d'entreprise
  - A : Personne physique (entreprise individuelle)
  - B : Personne morale (société)
- **NUMERO** : Numéro séquentiel

### Exemples par pays

| Pays | Exemple RCCM | Ville |
|------|--------------|-------|
| Cameroun | CM-DLA-2024-B-12345 | Douala |
| Sénégal | SN-DKR-2024-B-67890 | Dakar |
| Côte d'Ivoire | CI-ABJ-2024-B-11111 | Abidjan |
| Gabon | GA-LBV-2024-B-22222 | Libreville |
| Burkina Faso | BF-OUA-2024-B-33333 | Ouagadougou |
| Mali | ML-BKO-2024-B-44444 | Bamako |
| Togo | TG-LOM-2024-B-55555 | Lomé |
| Bénin | BJ-COT-2024-B-66666 | Cotonou |
| Congo | CG-BZV-2024-B-77777 | Brazzaville |
| Tchad | TD-NDJ-2024-B-88888 | N'Djaména |
| RCA | CF-BGI-2024-B-99999 | Bangui |
| Guinée Équatoriale | GQ-SSG-2024-B-10101 | Malabo |
| Niger | NE-NIA-2024-B-20202 | Niamey |
| Guinée-Bissau | GW-BXO-2024-B-30303 | Bissau |
| Comores | KM-MOR-2024-B-40404 | Moroni |
| Guinée | GN-CKY-2024-B-50505 | Conakry |
| RD Congo | CD-KIN-2024-B-60606 | Kinshasa |

## Autres Identifiants par Pays

### 1. Cameroun 🇨🇲
- **RCCM** : Format standard OHADA
- **NUI** : Numéro Unique d'Identification (14 caractères alphanumériques)
- **Numéro de Contribuable** : Pour les obligations fiscales

### 2. Sénégal 🇸🇳
- **RCCM** : Format standard OHADA
- **NINEA** : Numéro d'Identification Nationale des Entreprises et Associations (9 chiffres)
  - Obligatoire pour toutes les entreprises
  - Format : XXXXXXXXX

### 3. Côte d'Ivoire 🇨🇮
- **RCCM** : Format standard OHADA
- **CC** : Compte Contribuable (identifiant fiscal)

### 4. Gabon 🇬🇦
- **RCCM** : Format standard OHADA
- **NUI** : Numéro Unique d'Identification (13 caractères)

### 5. Burkina Faso 🇧🇫
- **RCCM** : Format standard OHADA
- **IFU** : Identifiant Financier Unique (12 chiffres)

### 6. Bénin 🇧🇯
- **RCCM** : Format standard OHADA
- **IFU** : Identifiant Fiscal Unique (13 caractères)

## Codes des Villes Principales

### Zone CEMAC (XAF)

#### Cameroun
- DLA : Douala
- YDE : Yaoundé
- GAR : Garoua
- BAF : Bafoussam
- BDA : Bamenda

#### Gabon
- LBV : Libreville
- POG : Port-Gentil
- FRA : Franceville
- OYE : Oyem

#### Congo
- BZV : Brazzaville
- PNR : Pointe-Noire
- DLS : Dolisie

#### Tchad
- NDJ : N'Djaména
- MND : Moundou
- SAR : Sarh
- ABE : Abéché

### Zone UEMOA (XOF)

#### Sénégal
- DKR : Dakar
- THI : Thiès
- KAO : Kaolack
- SLN : Saint-Louis

#### Côte d'Ivoire
- ABJ : Abidjan
- BVE : Bouaké
- YAM : Yamoussoukro
- DLO : Daloa

#### Burkina Faso
- OUA : Ouagadougou
- BOB : Bobo-Dioulasso
- KDG : Koudougou

#### Mali
- BKO : Bamako
- SIK : Sikasso
- KAY : Kayes
- SEG : Ségou

#### Togo
- LOM : Lomé
- SOK : Sokodé
- KAR : Kara

#### Bénin
- COT : Cotonou
- PNV : Porto-Novo
- PAR : Parakou

## Validation dans l'Application

L'application valide automatiquement les formats selon le pays :

```javascript
// Exemple de saisie pour le Cameroun
{
  "pays_code": "CM",
  "siret": "CM-DLA-2024-B-12345"  // RCCM
  // ou
  "siret": "12345678901234"  // NUI
}

// Exemple pour le Sénégal
{
  "pays_code": "SN",
  "siret": "123456789"  // NINEA
  // ou
  "siret": "SN-DKR-2024-B-12345"  // RCCM
}
```

## Conseils pour l'Inscription

1. **Choisissez le bon format** : RCCM pour les sociétés formelles, autres identifiants pour les obligations fiscales

2. **Codes de ville** : Utilisez le code à 3 lettres de la ville d'enregistrement

3. **Type d'entreprise** :
   - A : Pour les entreprises individuelles
   - B : Pour les sociétés (SARL, SA, etc.)

4. **Année** : Utilisez l'année d'enregistrement au RCCM

5. **Validation** : L'application valide automatiquement le format selon le pays sélectionné

## Migration des Données

Pour les cabinets existants qui migrent vers l'application :
- Les anciens numéros SIRET français restent valides
- Les RCCM peuvent être saisis dans le nouveau format
- Les identifiants fiscaux (NINEA, IFU, etc.) sont acceptés
- Possibilité de mettre à jour ultérieurement via les paramètres