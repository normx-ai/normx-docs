#!/usr/bin/env python3
"""
Script pour populer la table documents_requis avec les documents nécessaires
selon le type de dossier et les échéances existantes.

Les documents requis sont organisés par mois comme les échéances.
"""

import sys
import os
from typing import List, Dict

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.dossier import Dossier, TypeDossier
from app.models.echeance import Echeance
from app.models.document_requis import DocumentRequis
from app.models.document import TypeDocument


def get_documents_requis_by_type(type_dossier: TypeDossier) -> List[TypeDocument]:
    """
    Retourne la liste des types de documents requis selon le type de dossier
    """
    if type_dossier == TypeDossier.COMPTABILITE:
        return [
            TypeDocument.FACTURE_ACHAT,
            TypeDocument.FACTURE_VENTE,
            TypeDocument.RELEVE_BANCAIRE,
        ]
    elif type_dossier == TypeDossier.PAIE:
        return [
            TypeDocument.ETAT_PAIE,
            TypeDocument.DECLARATION_SOCIALE,
        ]
    elif type_dossier == TypeDossier.FISCALITE:
        return [
            TypeDocument.DECLARATION_IMPOT,
            TypeDocument.DECLARATION_TVA,
        ]
    else:
        # Pour les autres types, documents de base
        return [
            TypeDocument.COURRIER,
            TypeDocument.CONTRAT,
        ]


def populate_documents_requis():
    """
    Popule la table documents_requis avec les documents nécessaires
    pour tous les dossiers et échéances existants
    """
    db = SessionLocal()
    
    try:
        # Récupérer tous les dossiers avec leurs échéances
        dossiers = db.query(Dossier).all()
        
        print(f"=== POPULATION DES DOCUMENTS REQUIS ===")
        print(f"Nombre de dossiers trouvés: {len(dossiers)}")
        
        total_documents_crees = 0
        
        for dossier in dossiers:
            print(f"\n--- Dossier {dossier.id}: {dossier.reference} ({dossier.type_dossier}) ---")
            
            # Récupérer les échéances pour ce dossier
            echeances = db.query(Echeance).filter(Echeance.dossier_id == dossier.id).all()
            print(f"Échéances trouvées: {len(echeances)}")
            
            # Obtenir les types de documents requis pour ce type de dossier
            types_documents = get_documents_requis_by_type(dossier.type_dossier)
            print(f"Types de documents requis: {[doc.value for doc in types_documents]}")
            
            documents_dossier = 0
            
            # Pour chaque échéance, créer les documents requis
            for echeance in echeances:
                print(f"  Échéance {echeance.id}: {echeance.periode_label}")
                
                # Pour chaque type de document requis
                for type_doc in types_documents:
                    # Vérifier si le document requis existe déjà
                    existing = db.query(DocumentRequis).filter(
                        DocumentRequis.dossier_id == dossier.id,
                        DocumentRequis.echeance_id == echeance.id,
                        DocumentRequis.type_document == type_doc
                    ).first()
                    
                    if existing:
                        print(f"    - {type_doc.value}: EXISTE DÉJÀ")
                        continue
                    
                    # Créer le document requis
                    doc_requis = DocumentRequis(
                        dossier_id=dossier.id,
                        echeance_id=echeance.id,
                        type_document=type_doc,
                        mois=echeance.mois,
                        annee=echeance.annee,
                        est_applicable=True,
                        est_fourni=False
                    )
                    
                    db.add(doc_requis)
                    documents_dossier += 1
                    total_documents_crees += 1
                    print(f"    - {type_doc.value}: CRÉÉ")
            
            print(f"Documents créés pour ce dossier: {documents_dossier}")
        
        # Sauvegarder les changements
        db.commit()
        print(f"\n=== RÉSUMÉ ===")
        print(f"Total documents requis créés: {total_documents_crees}")
        print("Population terminée avec succès!")
        
    except Exception as e:
        db.rollback()
        print(f"Erreur lors de la population: {e}")
        raise
    finally:
        db.close()


def verify_population():
    """
    Vérifie que la population s'est bien déroulée
    """
    db = SessionLocal()
    
    try:
        print(f"\n=== VÉRIFICATION ===")
        
        # Compter les documents requis par dossier
        dossiers = db.query(Dossier).all()
        
        for dossier in dossiers:
            count = db.query(DocumentRequis).filter(
                DocumentRequis.dossier_id == dossier.id
            ).count()
            
            echeances_count = db.query(Echeance).filter(
                Echeance.dossier_id == dossier.id
            ).count()
            
            types_documents = get_documents_requis_by_type(dossier.type_dossier)
            expected_count = echeances_count * len(types_documents)
            
            print(f"Dossier {dossier.id} ({dossier.type_dossier}):")
            print(f"  - Échéances: {echeances_count}")
            print(f"  - Types documents: {len(types_documents)}")
            print(f"  - Documents requis attendus: {expected_count}")
            print(f"  - Documents requis créés: {count}")
            
            if count == expected_count:
                print(f"  ✓ OK")
            else:
                print(f"  ⚠ PROBLÈME: attendu {expected_count}, trouvé {count}")
        
        # Statistiques globales
        total_docs = db.query(DocumentRequis).count()
        print(f"\nTotal documents requis en base: {total_docs}")
        
    finally:
        db.close()


def show_details():
    """
    Affiche le détail des documents requis créés
    """
    db = SessionLocal()
    
    try:
        print(f"\n=== DÉTAIL DES DOCUMENTS REQUIS ===")
        
        documents = db.query(DocumentRequis).join(
            Echeance, DocumentRequis.echeance_id == Echeance.id
        ).join(
            Dossier, DocumentRequis.dossier_id == Dossier.id
        ).order_by(Dossier.id, Echeance.mois, DocumentRequis.type_document).all()
        
        current_dossier = None
        current_echeance = None
        
        for doc in documents:
            if current_dossier != doc.dossier_id:
                current_dossier = doc.dossier_id
                print(f"\n--- Dossier {doc.dossier.reference} ({doc.dossier.type_dossier}) ---")
            
            if current_echeance != doc.echeance_id:
                current_echeance = doc.echeance_id
                print(f"  {doc.echeance.periode_label}:")
            
            statut = "✓ FOURNI" if doc.est_fourni else "○ À FOURNIR"
            applicable = "" if doc.est_applicable else " [NON APPLICABLE]"
            print(f"    - {doc.type_document.value}: {statut}{applicable}")
        
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Popule les documents requis")
    parser.add_argument("--verify", action="store_true", help="Vérifie seulement")
    parser.add_argument("--details", action="store_true", help="Affiche le détail")
    parser.add_argument("--force", action="store_true", help="Force la recréation")
    
    args = parser.parse_args()
    
    if args.verify:
        verify_population()
    elif args.details:
        show_details()
    else:
        populate_documents_requis()
        verify_population()
        
        if args.details:
            show_details()