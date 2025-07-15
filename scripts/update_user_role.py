#!/usr/bin/env python3
"""
Script pour mettre à jour le rôle d'un utilisateur
"""
import os
import sys
from pathlib import Path

# Ajouter le répertoire parent au path Python
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User


def update_user_role(username: str, new_role: str):
    """Met à jour le rôle d'un utilisateur"""
    db = SessionLocal()
    
    try:
        # Trouver l'utilisateur
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            print(f"Utilisateur '{username}' non trouvé")
            return False
        
        # Mettre à jour le rôle
        old_role = user.role
        user.role = new_role
        db.commit()
        
        print(f"Rôle de l'utilisateur '{username}' mis à jour : {old_role} → {new_role}")
        return True
        
    except Exception as e:
        print(f"Erreur : {e}")
        db.rollback()
        return False
    finally:
        db.close()


def list_users():
    """Liste tous les utilisateurs"""
    db = SessionLocal()
    
    try:
        users = db.query(User).all()
        print("\nUtilisateurs existants :")
        print("-" * 50)
        for user in users:
            print(f"- {user.username} ({user.email}) - Rôle: {user.role}")
        print("-" * 50)
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            list_users()
        elif len(sys.argv) == 3:
            username = sys.argv[1]
            new_role = sys.argv[2]
            if new_role not in ["admin", "manager", "collaborateur"]:
                print("Erreur : Le rôle doit être 'admin', 'manager' ou 'collaborateur'")
            else:
                update_user_role(username, new_role)
        else:
            print("Usage : python update_user_role.py <username> <role>")
            print("        python update_user_role.py list")
    else:
        # Mode interactif
        list_users()
        username = input("\nNom d'utilisateur à modifier : ")
        new_role = input("Nouveau rôle (admin/manager/collaborateur) : ")
        
        if new_role in ["admin", "manager", "collaborateur"]:
            update_user_role(username, new_role)
        else:
            print("Rôle invalide")