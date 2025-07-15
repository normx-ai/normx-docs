#!/usr/bin/env python3
"""
Script pour tester les tâches Celery
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.tasks import (
    check_all_notifications,
    send_notification_email,
    cleanup_old_notifications,
    update_echeances_status
)

def test_tasks():
    print("🧪 Test des tâches Celery\n")
    
    # Test 1: Vérification des notifications
    print("1️⃣ Test de check_all_notifications...")
    try:
        result = check_all_notifications.apply_async()
        print(f"   Tâche lancée avec ID: {result.id}")
        print("   Utilisez 'celery -A app.core.celery_app inspect active' pour voir l'état")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test 2: Envoi d'email de test
    print("\n2️⃣ Test de send_notification_email...")
    try:
        result = send_notification_email.apply_async(
            args=[
                "test@example.com",
                "Test Celery",
                "test",
                {"user_name": "Test User", "message": "Test depuis Celery"}
            ]
        )
        print(f"   Tâche lancée avec ID: {result.id}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test 3: Nettoyage
    print("\n3️⃣ Test de cleanup_old_notifications...")
    try:
        result = cleanup_old_notifications.apply_async()
        print(f"   Tâche lancée avec ID: {result.id}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test 4: Mise à jour des statuts
    print("\n4️⃣ Test de update_echeances_status...")
    try:
        result = update_echeances_status.apply_async()
        print(f"   Tâche lancée avec ID: {result.id}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    print("\n✅ Tests terminés!")
    print("\nPour voir l'état des tâches:")
    print("  - celery -A app.core.celery_app inspect active")
    print("  - celery -A app.core.celery_app inspect scheduled")
    print("  - celery -A app.core.celery_app inspect stats")

if __name__ == "__main__":
    test_tasks()