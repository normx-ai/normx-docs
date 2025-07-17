#!/usr/bin/env python3
"""
Script pour créer un utilisateur admin et un cabinet initial
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models import User, Cabinet
from app.core.security import get_password_hash
from datetime import datetime
import argparse

def create_admin_user(email: str, password: str, cabinet_name: str):
    db = SessionLocal()
    try:
        # Vérifier si l'utilisateur existe déjà
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"L'utilisateur {email} existe déjà")
            return
        
        # Créer le cabinet
        cabinet = Cabinet(
            name=cabinet_name,
            address="123 Rue Example",
            phone="0123456789",
            email=email,
            tax_number="FR12345678901",
            registration_number="RCS123456789",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(cabinet)
        db.flush()
        
        # Créer l'utilisateur admin
        admin_user = User(
            email=email,
            hashed_password=get_password_hash(password),
            full_name="Administrateur",
            is_active=True,
            is_admin=True,
            cabinet_id=cabinet.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(admin_user)
        db.commit()
        
        print(f"✓ Cabinet '{cabinet_name}' créé avec succès")
        print(f"✓ Utilisateur admin '{email}' créé avec succès")
        
    except Exception as e:
        db.rollback()
        print(f"Erreur lors de la création: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Créer un utilisateur admin")
    parser.add_argument("--email", default="admin@normx-ai.com", help="Email de l'admin")
    parser.add_argument("--password", default="Admin123!", help="Mot de passe")
    parser.add_argument("--cabinet", default="Cabinet NormX", help="Nom du cabinet")
    
    args = parser.parse_args()
    
    print(f"Création de l'utilisateur admin...")
    create_admin_user(args.email, args.password, args.cabinet)