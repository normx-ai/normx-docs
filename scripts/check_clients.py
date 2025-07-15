#!/usr/bin/env python3
"""
Script pour vérifier les clients dans la base de données
"""
import os
import sys
from pathlib import Path

# Ajouter le répertoire parent au path Python
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.client import Client


def check_clients():
    """Vérifie les clients dans la base de données"""
    db = SessionLocal()
    
    try:
        # Compter les clients
        count = db.query(Client).count()
        print(f"Nombre total de clients: {count}")
        
        # Lister les premiers clients
        clients = db.query(Client).limit(10).all()
        print("\nPremiers clients:")
        for client in clients:
            print(f"- {client.numero_client}: {client.nom} ({client.forme_juridique}) - SIRET: {client.siret or 'Non renseigné'}")
        
        if count > 10:
            print(f"... et {count - 10} autres clients")
            
    except Exception as e:
        print(f"Erreur lors de la vérification: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    check_clients()