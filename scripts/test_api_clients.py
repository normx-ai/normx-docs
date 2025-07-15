#!/usr/bin/env python3
"""
Script pour tester l'API des clients
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

def test_clients_api():
    """Tester l'API des clients"""
    token = get_token()
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Récupérer la liste des clients
    print("=== Test 1: GET /api/v1/clients ===")
    response = requests.get(f"{API_URL}/api/v1/clients", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        clients = response.json()
        print(f"Nombre de clients: {len(clients)}")
        if clients:
            print("\nPremiers clients:")
            for client in clients[:5]:
                print(f"- {client['numero_client']}: {client['nom']} ({client['forme_juridique']})")
    else:
        print("Erreur:", response.text)

if __name__ == "__main__":
    test_clients_api()