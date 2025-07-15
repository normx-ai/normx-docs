#!/usr/bin/env python3
"""
Script pour obtenir le cabinet par défaut
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.cabinet import Cabinet
from app.core.config import settings

def get_default_cabinet():
    # Créer la connexion à la base de données
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Récupérer le cabinet par défaut
        cabinet = db.query(Cabinet).filter(Cabinet.slug == "cabinet-principal").first()
        
        if cabinet:
            print(f"Cabinet par défaut trouvé:")
            print(f"  ID: {cabinet.id}")
            print(f"  Nom: {cabinet.nom}")
            print(f"  Slug: {cabinet.slug}")
            print(f"  Plan: {cabinet.plan}")
            print(f"  Max users: {cabinet.max_users}")
            print(f"  Max clients: {cabinet.max_clients}")
            print(f"  Actif: {cabinet.is_active}")
            
            # Compter les utilisateurs
            from app.models.user import User
            user_count = db.query(User).filter(User.cabinet_id == cabinet.id).count()
            print(f"  Utilisateurs actuels: {user_count}")
            
            # Compter les clients
            from app.models.client import Client
            client_count = db.query(Client).filter(Client.cabinet_id == cabinet.id).count()
            print(f"  Clients actuels: {client_count}")
            
            # Compter les dossiers
            from app.models.dossier import Dossier
            dossier_count = db.query(Dossier).filter(Dossier.cabinet_id == cabinet.id).count()
            print(f"  Dossiers actuels: {dossier_count}")
            
            return cabinet.id
        else:
            print("Aucun cabinet par défaut trouvé!")
            return None
            
    finally:
        db.close()

if __name__ == "__main__":
    cabinet_id = get_default_cabinet()
    if cabinet_id:
        print(f"\nUtilisez cabinet_id={cabinet_id} pour vos tests")