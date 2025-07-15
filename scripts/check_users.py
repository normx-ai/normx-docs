#!/usr/bin/env python3
"""
Script pour vérifier les utilisateurs dans la base
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.models.user import User

def check_users():
    db = SessionLocal()
    
    users = db.query(User).all()
    print(f"Nombre d'utilisateurs: {len(users)}")
    
    for user in users:
        print(f"- Username: {user.username}, Email: {user.email}, Cabinet: {user.cabinet_name}")
    
    db.close()

if __name__ == "__main__":
    check_users()