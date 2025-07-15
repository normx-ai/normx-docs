#!/usr/bin/env python3
"""
Script pour tester l'API des dossiers
"""
import requests
import json

# Configuration
API_URL = "http://localhost:8000"
USERNAME = "mzitoun"
PASSWORD = "Cabinet16"

def get_token():
    """Obtenir un token JWT"""
    response = requests.post(
        f"{API_URL}/api/v1/auth/token",
        data={"username": USERNAME, "password": PASSWORD}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Erreur d'authentification: {response.status_code}")
        print(response.text)
        return None

def test_dossiers_api():
    """Tester l'API des dossiers"""
    token = get_token()
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Récupérer la liste des dossiers
    print("=== Test 1: GET /api/v1/dossiers ===")
    response = requests.get(f"{API_URL}/api/v1/dossiers", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        dossiers = response.json()
        print(f"Nombre de dossiers: {len(dossiers)}")
        if dossiers:
            print("Premier dossier:", json.dumps(dossiers[0], indent=2))
    else:
        print("Erreur:", response.text)
    
    # Test 2: Vérifier les données dans la base
    print("\n=== Test 2: Vérification directe ===")
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    
    from app.core.database import SessionLocal
    from app.models.dossier import Dossier
    
    db = SessionLocal()
    count = db.query(Dossier).count()
    print(f"Nombre de dossiers dans la base: {count}")
    
    if count > 0:
        dossier = db.query(Dossier).first()
        print(f"Premier dossier: {dossier.reference} - {dossier.nom_client}")
    
    db.close()

if __name__ == "__main__":
    test_dossiers_api()