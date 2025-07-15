# Script de Population des Documents Requis

Ce script permet de peupler automatiquement la table `documents_requis` avec les documents nécessaires selon les types de dossiers et échéances existants.

## Fonctionnalités

Le script génère automatiquement les documents requis pour chaque échéance mensuelle selon le type de dossier:

### Types de documents par dossier

- **COMPTABILITE**: 
  - Factures d'achat
  - Factures de vente  
  - Relevés bancaires

- **PAIE**:
  - États de paie
  - Déclarations sociales

- **FISCALITE**:
  - Déclarations d'impôt
  - Déclarations TVA

- **Autres types**:
  - Courriers
  - Contrats

## Utilisation

### Exécution standard
```bash
cd /home/chris/gd-ia-comptable
python3 scripts/populate_documents_requis.py
```

### Options disponibles

#### Vérification seulement
```bash
python3 scripts/populate_documents_requis.py --verify
```
Vérifie les documents requis existants sans en créer de nouveaux.

#### Affichage détaillé
```bash
python3 scripts/populate_documents_requis.py --details
```
Affiche le détail complet de tous les documents requis par dossier et échéance.

#### Exécution avec détails
```bash
python3 scripts/populate_documents_requis.py --details
```
Execute le script principal puis affiche les détails.

## Structure des données créées

Chaque document requis créé contient:
- `dossier_id`: ID du dossier concerné
- `echeance_id`: ID de l'échéance mensuelle
- `type_document`: Type selon l'énumération TypeDocument
- `mois`: Mois de l'échéance (1-12)
- `annee`: Année de l'échéance
- `est_applicable`: True (applicable par défaut)
- `est_fourni`: False (non fourni par défaut)

## Logique de création

Le script:
1. Récupère tous les dossiers existants
2. Pour chaque dossier, identifie ses échéances mensuelles
3. Détermine les types de documents requis selon le type de dossier
4. Crée un document requis pour chaque combinaison (échéance × type de document)
5. Évite les doublons en vérifiant l'existence avant création

## Exemple de sortie

```
=== POPULATION DES DOCUMENTS REQUIS ===
Nombre de dossiers trouvés: 3

--- Dossier 167: COMPTA-2025-0001 (COMPTABILITE) ---
Échéances trouvées: 12
Types de documents requis: ['FACTURE_ACHAT', 'FACTURE_VENTE', 'RELEVE_BANCAIRE']
  Échéance 37: Janvier 2025
    - FACTURE_ACHAT: CRÉÉ
    - FACTURE_VENTE: CRÉÉ
    - RELEVE_BANCAIRE: CRÉÉ
Documents créés pour ce dossier: 36

=== RÉSUMÉ ===
Total documents requis créés: 108
Population terminée avec succès!
```

## Sécurité

- Le script vérifie les doublons avant création
- Utilise des transactions pour éviter les états incohérents
- Rollback automatique en cas d'erreur
- Ne supprime jamais de données existantes