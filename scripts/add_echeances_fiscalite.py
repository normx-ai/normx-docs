#!/usr/bin/env python3
"""
Script pour ajouter les échéances mensuelles aux dossiers FISCALITE
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.dossier import Dossier, TypeDossier
from app.models.echeance import Echeance
from app.models.saisie import SaisieComptable
from datetime import datetime as dt


def add_echeances_fiscalite():
    """Ajouter les échéances mensuelles aux dossiers FISCALITE"""
    
    db = next(get_db())
    
    try:
        print("=== AJOUT DES ÉCHÉANCES FISCALITÉ ===")
        
        # Trouver tous les dossiers FISCALITE
        dossiers_fiscalite = db.query(Dossier).filter(
            Dossier.type_dossier == TypeDossier.FISCALITE
        ).all()
        
        print(f"Dossiers FISCALITE trouvés: {len(dossiers_fiscalite)}")
        
        if not dossiers_fiscalite:
            print("Aucun dossier FISCALITE trouvé")
            return
        
        # Mois en français
        mois_noms = [
            'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
            'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
        ]
        
        # Types de saisies pour FISCALITE
        types_saisies_fiscalite = ['TVA', 'DECLARATIONS', 'AUTRES_TAXES']
        
        total_created = 0
        
        for dossier in dossiers_fiscalite:
            print(f"\n--- Dossier {dossier.reference} ({dossier.nom_client}) ---")
            
            # Vérifier si des échéances existent déjà
            echeances_existantes = db.query(Echeance).filter(
                Echeance.dossier_id == dossier.id
            ).count()
            
            if echeances_existantes > 0:
                print(f"  {echeances_existantes} échéances existent déjà - ignoré")
                continue
            
            # Déterminer l'année
            annee_depart = dt.now().year
            if dossier.exercice_fiscal:
                try:
                    annee_depart = int(dossier.exercice_fiscal)
                except:
                    pass
            
            print(f"  Création des échéances pour l'année {annee_depart}")
            
            # Créer une échéance pour chaque mois
            for mois_idx in range(12):
                mois_num = mois_idx + 1
                periode_label = f"{mois_noms[mois_idx]} {annee_depart}"
                
                # Date d'échéance au 15 du mois suivant (standard TVA)
                mois_echeance = mois_num + 1
                annee_echeance = annee_depart
                
                if mois_echeance > 12:
                    mois_echeance = 1
                    annee_echeance += 1
                
                date_echeance = dt(annee_echeance, mois_echeance, 15).date()
                
                # Créer l'échéance
                echeance = Echeance(
                    dossier_id=dossier.id,
                    mois=mois_num,
                    annee=annee_depart,
                    periode_label=periode_label,
                    date_echeance=date_echeance,
                    statut='A_FAIRE'
                )
                db.add(echeance)
                db.flush()
                
                # Créer les saisies pour cette échéance
                for type_saisie in types_saisies_fiscalite:
                    saisie = SaisieComptable(
                        dossier_id=dossier.id,
                        echeance_id=echeance.id,
                        type_journal=type_saisie,
                        mois=mois_num,
                        annee=annee_depart,
                        est_complete=False
                    )
                    db.add(saisie)
                
                print(f"    ✓ {periode_label} - échéance {date_echeance}")
            
            total_created += 12
        
        print(f"\n=== RÉSUMÉ ===")
        print(f"Total échéances créées: {total_created}")
        
        confirm = input("Confirmer la création ? (oui/non): ").lower().strip()
        
        if confirm in ['oui', 'o', 'yes', 'y']:
            db.commit()
            print("✅ Création terminée avec succès!")
        else:
            db.rollback()
            print("❌ Création annulée")
            
    except Exception as e:
        print(f"❌ Erreur lors de la création: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def verify_echeances():
    """Vérifier les échéances après création"""
    
    db = next(get_db())
    
    try:
        print("\n=== VÉRIFICATION ===")
        
        dossiers_fiscalite = db.query(Dossier).filter(
            Dossier.type_dossier == TypeDossier.FISCALITE
        ).all()
        
        for dossier in dossiers_fiscalite:
            echeances = db.query(Echeance).filter(
                Echeance.dossier_id == dossier.id
            ).all()
            
            print(f"\nDossier {dossier.reference}: {len(echeances)} échéances")
            
            if echeances:
                # Afficher les 3 premières
                for echeance in echeances[:3]:
                    saisies = db.query(SaisieComptable).filter(
                        SaisieComptable.echeance_id == echeance.id
                    ).all()
                    types_saisies = [s.type_journal for s in saisies]
                    print(f"  - {echeance.periode_label}: {types_saisies}")
                    
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    add_echeances_fiscalite()
    verify_echeances()