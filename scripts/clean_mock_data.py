#!/usr/bin/env python3
"""
Script pour supprimer toutes les données mockées
"""
import os
import sys
from pathlib import Path

# Ajouter le répertoire parent au path Python
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.dossier import Dossier
from app.models.alerte import Alerte
from app.models.historique import HistoriqueDossier
from app.models.document import Document


def clean_mock_data():
    """Supprime toutes les données mockées des dossiers"""
    db = SessionLocal()
    
    try:
        # Supprimer toutes les alertes
        deleted_alertes = db.query(Alerte).delete()
        print(f"Supprimé {deleted_alertes} alertes")
        
        # Supprimer tout l'historique
        deleted_historique = db.query(HistoriqueDossier).delete()
        print(f"Supprimé {deleted_historique} entrées d'historique")
        
        # Supprimer tous les documents
        deleted_documents = db.query(Document).delete()
        print(f"Supprimé {deleted_documents} documents")
        
        # Supprimer tous les dossiers
        deleted_dossiers = db.query(Dossier).delete()
        print(f"Supprimé {deleted_dossiers} dossiers")
        
        # Commit des changements
        db.commit()
        print("\nToutes les données mockées ont été supprimées avec succès!")
        print("Les clients restent dans la base de données.")
        
    except Exception as e:
        db.rollback()
        print(f"Erreur lors de la suppression: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    clean_mock_data()