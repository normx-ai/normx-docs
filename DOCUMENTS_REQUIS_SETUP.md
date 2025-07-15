# Configuration des Documents Requis

## Résumé

Système complet pour populer automatiquement la table `documents_requis` avec les documents nécessaires selon les types de dossiers et échéances existants.

## Fichiers créés

### Scripts principaux

1. **`/home/chris/gd-ia-comptable/scripts/populate_documents_requis.py`**
   - Script Python principal pour la population des documents requis
   - Utilise les modèles SQLAlchemy existants
   - Gestion des erreurs et transactions
   - Options : `--verify`, `--details`, `--force`

2. **`/home/chris/gd-ia-comptable/scripts/test_populate_dry_run.py`**
   - Script de test en mode simulation
   - Aucune modification de base de données
   - Validation de la logique avant exécution

3. **`/home/chris/gd-ia-comptable/scripts/run_populate_documents.sh`**
   - Script shell pour faciliter l'exécution
   - Gestion automatique de l'environnement virtuel
   - Interface utilisateur simplifiée

### Documentation

4. **`/home/chris/gd-ia-comptable/scripts/README_populate_documents.md`**
   - Documentation détaillée du système
   - Exemples d'utilisation
   - Explication de la logique

## Logique de création

### Types de documents par dossier

- **COMPTABILITE** : Factures d'achat, Factures de vente, Relevés bancaires
- **PAIE** : États de paie, Déclarations sociales  
- **FISCALITE** : Déclarations d'impôt, Déclarations TVA
- **Autres** : Courriers, Contrats

### Structure des données

Chaque document requis créé contient :
- `dossier_id` : ID du dossier concerné
- `echeance_id` : ID de l'échéance mensuelle
- `type_document` : Type selon l'énumération TypeDocument
- `mois` et `annee` : Période de l'échéance
- `est_applicable` : True par défaut
- `est_fourni` : False par défaut

## Utilisation

### Test de simulation (recommandé en premier)
```bash
cd /home/chris/gd-ia-comptable
scripts/run_populate_documents.sh test
```

### Exécution normale
```bash
scripts/run_populate_documents.sh
```

### Vérification des résultats
```bash
scripts/run_populate_documents.sh verify
```

### Affichage détaillé
```bash
scripts/run_populate_documents.sh details
```

## Résultats attendus

D'après l'analyse des logs :

### Dossiers existants
- **Dossier 167** : COMPTA-2025-0001 (COMPTABILITE) - 12 échéances
- **Dossier 168** : FISCAL-2025-0001 (FISCALITE) - 0 échéance mensuelle 
- **Dossier 169** : PAIE-2025-0001 (PAIE) - 12 échéances

### Documents requis à créer
- **Dossier COMPTABILITE** : 12 échéances × 3 types = 36 documents
- **Dossier PAIE** : 12 échéances × 2 types = 24 documents
- **Total attendu** : 60 documents requis

## Sécurité et robustesse

- **Vérification des doublons** : Le script vérifie l'existence avant création
- **Transactions** : Rollback automatique en cas d'erreur
- **Non-destructif** : Ne supprime jamais de données existantes
- **Validation** : Test dry-run pour vérifier la logique

## Intégration avec l'application

Les documents requis créés s'intègrent directement avec :
- L'API `/api/v1/dossiers/{id}/documents-requis`
- L'interface utilisateur de gestion des documents
- Le système de suivi des échéances

## Maintenance future

Pour ajouter de nouveaux types de documents ou modifier la logique :
1. Modifier la fonction `get_documents_requis_by_type()` dans le script principal
2. Tester avec le script de simulation
3. Exécuter la population pour les nouveaux dossiers

## Support

En cas de problème :
1. Vérifier les logs d'erreur
2. Utiliser l'option `--verify` pour diagnostiquer
3. Tester avec le script de simulation
4. Consulter la documentation détaillée dans `README_populate_documents.md`