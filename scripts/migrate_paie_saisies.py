#!/usr/bin/env python3
"""
Script de migration pour corriger les saisies des dossiers PAIE
Remplace les saisies comptables par les saisies de paie appropriées
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.dossier import Dossier, TypeDossier
from app.models.echeance import Echeance
from app.models.saisie import SaisieComptable


def migrate_paie_saisies():
    """Migration des saisies pour les dossiers PAIE"""
    
    db = next(get_db())
    
    try:
        print("=== MIGRATION DES SAISIES PAIE ===")
        
        # Trouver tous les dossiers PAIE
        dossiers_paie = db.query(Dossier).filter(
            Dossier.type_dossier == TypeDossier.PAIE
        ).all()
        
        print(f"Dossiers PAIE trouvés: {len(dossiers_paie)}")
        
        if not dossiers_paie:
            print("Aucun dossier PAIE à migrer")
            return
        
        # Types de saisies PAIE corrects
        types_saisies_paie = ['DSN', 'BULLETINS', 'DUCS', 'DECLARATION_SOCIALE', 'CHARGES_SOCIALES']
        
        # Types de saisies comptables incorrects (à supprimer)
        types_saisies_comptables = ['BANQUE', 'CAISSE', 'OD', 'ACHATS', 'VENTES', 'PAIE']
        
        total_modified = 0
        
        for dossier in dossiers_paie:
            print(f"\n--- Dossier {dossier.reference} ({dossier.nom_client}) ---")
            
            # Récupérer les échéances de ce dossier
            echeances = db.query(Echeance).filter(
                Echeance.dossier_id == dossier.id
            ).all()
            
            print(f"Échéances trouvées: {len(echeances)}")
            
            for echeance in echeances:
                print(f"  Échéance {echeance.periode_label}")
                
                # Récupérer les saisies existantes
                saisies_existantes = db.query(SaisieComptable).filter(
                    SaisieComptable.echeance_id == echeance.id
                ).all()
                
                # Identifier les saisies incorrectes
                saisies_incorrectes = [
                    s for s in saisies_existantes 
                    if s.type_journal in types_saisies_comptables
                ]
                
                # Identifier les saisies correctes déjà présentes
                saisies_correctes_existantes = [
                    s.type_journal for s in saisies_existantes 
                    if s.type_journal in types_saisies_paie
                ]
                
                if saisies_incorrectes:
                    print(f"    Saisies incorrectes trouvées: {[s.type_journal for s in saisies_incorrectes]}")
                    
                    # Supprimer les saisies incorrectes
                    for saisie in saisies_incorrectes:
                        print(f"    Suppression: {saisie.type_journal}")
                        db.delete(saisie)
                    
                    # Créer les saisies PAIE manquantes
                    for type_journal in types_saisies_paie:
                        if type_journal not in saisies_correctes_existantes:
                            nouvelle_saisie = SaisieComptable(
                                dossier_id=dossier.id,
                                echeance_id=echeance.id,
                                type_journal=type_journal,
                                mois=echeance.mois,
                                annee=echeance.annee,
                                est_complete=False
                            )
                            db.add(nouvelle_saisie)
                            print(f"    Création: {type_journal}")
                    
                    total_modified += 1
                else:
                    print(f"    Saisies correctes: {saisies_correctes_existantes}")
        
        # Confirmer les changements
        if total_modified > 0:
            print(f"\n=== RÉSUMÉ ===")
            print(f"Échéances modifiées: {total_modified}")
            confirm = input("Confirmer la migration ? (oui/non): ").lower().strip()
            
            if confirm in ['oui', 'o', 'yes', 'y']:
                db.commit()
                print("✅ Migration terminée avec succès!")
            else:
                db.rollback()
                print("❌ Migration annulée")
        else:
            print("✅ Aucune modification nécessaire")
            
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def verify_paie_saisies():
    """Vérifier les saisies après migration"""
    
    db = next(get_db())
    
    try:
        print("\n=== VÉRIFICATION POST-MIGRATION ===")
        
        dossiers_paie = db.query(Dossier).filter(
            Dossier.type_dossier == TypeDossier.PAIE
        ).all()
        
        types_saisies_paie = ['DSN', 'BULLETINS', 'DUCS', 'DECLARATION_SOCIALE', 'CHARGES_SOCIALES']
        types_saisies_comptables = ['BANQUE', 'CAISSE', 'OD', 'ACHATS', 'VENTES']
        
        for dossier in dossiers_paie:
            print(f"\nDossier {dossier.reference}:")
            
            echeances = db.query(Echeance).filter(
                Echeance.dossier_id == dossier.id
            ).all()
            
            for echeance in echeances[:3]:  # Vérifier les 3 premières échéances
                saisies = db.query(SaisieComptable).filter(
                    SaisieComptable.echeance_id == echeance.id
                ).all()
                
                types_presents = [s.type_journal for s in saisies]
                saisies_paie = [t for t in types_presents if t in types_saisies_paie]
                saisies_comptables = [t for t in types_presents if t in types_saisies_comptables]
                
                print(f"  {echeance.periode_label}:")
                print(f"    Saisies PAIE: {saisies_paie}")
                if saisies_comptables:
                    print(f"    ⚠️  Saisies comptables restantes: {saisies_comptables}")
                else:
                    print(f"    ✅ Aucune saisie comptable incorrecte")
                    
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migration des saisies PAIE")
    parser.add_argument("--verify", action="store_true", help="Vérifier seulement")
    parser.add_argument("--dry-run", action="store_true", help="Simulation sans modification")
    
    args = parser.parse_args()
    
    if args.verify:
        verify_paie_saisies()
    else:
        migrate_paie_saisies()
        verify_paie_saisies()