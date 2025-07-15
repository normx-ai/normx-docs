#!/usr/bin/env python3
"""
Script de démonstration des fonctionnalités de sécurité
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.security import (
    validate_password_strength,
    validate_email,
    validate_phone,
    validate_siret,
    validate_iban,
    sanitize_string,
    validate_file_extension,
    validate_file_size
)

def demo_security():
    print("🔐 Démonstration des fonctions de sécurité\n")
    
    # Test de validation des mots de passe
    print("1️⃣ Validation des mots de passe:")
    passwords = [
        "123456",  # Trop court
        "password123",  # Pas de majuscule ni caractère spécial
        "Password123",  # Pas de caractère spécial
        "Password123!",  # Valide
        "P@ssw0rd!"  # Valide
    ]
    
    for pwd in passwords:
        valid, msg = validate_password_strength(pwd)
        status = "✅" if valid else "❌"
        print(f"   {status} '{pwd}' - {msg if msg else 'Valide'}")
    
    # Test de validation des emails
    print("\n2️⃣ Validation des emails:")
    emails = [
        "user@example.com",  # Valide
        "invalid.email",  # Invalide
        "user@",  # Invalide
        "@example.com",  # Invalide
        "user.name+tag@example.co.uk"  # Valide
    ]
    
    for email in emails:
        valid = validate_email(email)
        status = "✅" if valid else "❌"
        print(f"   {status} {email}")
    
    # Test de validation des téléphones
    print("\n3️⃣ Validation des téléphones (français):")
    phones = [
        "0123456789",  # Valide
        "01 23 45 67 89",  # Valide (avec espaces)
        "+33123456789",  # Valide (format international)
        "123456789",  # Invalide (pas assez de chiffres)
        "0123456789012"  # Invalide (trop de chiffres)
    ]
    
    for phone in phones:
        valid = validate_phone(phone)
        status = "✅" if valid else "❌"
        print(f"   {status} {phone}")
    
    # Test de validation des SIRET
    print("\n4️⃣ Validation des SIRET:")
    sirets = [
        "80314979300020",  # Valide (OVH)
        "12345678901234",  # Invalide (mauvais checksum)
        "803 149 793 00020",  # Valide (avec espaces)
        "1234567890"  # Invalide (pas assez de chiffres)
    ]
    
    for siret in sirets:
        valid = validate_siret(siret)
        status = "✅" if valid else "❌"
        print(f"   {status} {siret}")
    
    # Test de validation des IBAN
    print("\n5️⃣ Validation des IBAN (français):")
    ibans = [
        "FR1420041010050500013M02606",  # Valide
        "FR14 2004 1010 0505 0001 3M02 606",  # Valide (avec espaces)
        "FR1420041010050500013M02607",  # Invalide (mauvais checksum)
        "FR142004101005"  # Invalide (trop court)
    ]
    
    for iban in ibans:
        valid = validate_iban(iban)
        status = "✅" if valid else "❌"
        print(f"   {status} {iban}")
    
    # Test de nettoyage des chaînes
    print("\n6️⃣ Nettoyage des chaînes:")
    strings = [
        "Normal text",
        "Text with   multiple   spaces",
        "Text\nwith\ncontrol\rcharacters",
        "<script>alert('XSS')</script>",
        "A" * 300  # Texte trop long
    ]
    
    for text in strings:
        clean = sanitize_string(text, max_length=50)
        print(f"   Original: '{text[:50]}...' -> Nettoyé: '{clean}'")
    
    # Test de validation des fichiers
    print("\n7️⃣ Validation des fichiers:")
    files = [
        ("document.pdf", 1024 * 1024),  # 1MB PDF
        ("image.jpg", 5 * 1024 * 1024),  # 5MB JPEG
        ("script.exe", 1024),  # EXE non autorisé
        ("huge.pdf", 20 * 1024 * 1024),  # 20MB (trop gros)
    ]
    
    allowed_extensions = ["pdf", "jpg", "jpeg", "png", "doc", "docx"]
    
    for filename, size in files:
        ext_valid = validate_file_extension(filename, allowed_extensions)
        size_valid = validate_file_size(size, max_size_mb=10)
        status = "✅" if ext_valid and size_valid else "❌"
        reason = []
        if not ext_valid:
            reason.append("extension non autorisée")
        if not size_valid:
            reason.append("taille excessive")
        
        size_mb = size / (1024 * 1024)
        print(f"   {status} {filename} ({size_mb:.1f}MB) {' - ' + ', '.join(reason) if reason else ''}")
    
    print("\n✅ Démonstration terminée!")

if __name__ == "__main__":
    demo_security()