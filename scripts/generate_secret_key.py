#!/usr/bin/env python3
"""
Script pour générer une clé secrète sécurisée
"""

import secrets
import string

def generate_secret_key(length=64):
    """Génère une clé secrète cryptographiquement sûre"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

if __name__ == "__main__":
    print("🔐 Génération d'une nouvelle SECRET_KEY...")
    print("\n" + "="*70)
    
    secret_key = generate_secret_key()
    print(f"SECRET_KEY={secret_key}")
    
    print("="*70)
    print("\n⚠️  IMPORTANT:")
    print("1. Copiez cette clé dans votre fichier .env")
    print("2. Ne la partagez JAMAIS")
    print("3. Ne la commitez JAMAIS dans git")
    print("4. Utilisez une clé différente pour chaque environnement (dev, staging, prod)")
    print("\n📝 Pour l'utiliser:")
    print("   - Ouvrez .env")
    print("   - Remplacez la ligne SECRET_KEY=... par la nouvelle clé")
    print("   - Redémarrez l'application")