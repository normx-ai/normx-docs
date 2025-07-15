#!/usr/bin/env python3
"""
Script pour tester le système de notifications
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.cabinet import Cabinet
from app.models.user import User
from app.core.config import settings
from app.services.notification_service import NotificationService
from app.services.email_service import email_service

async def test_notifications():
    # Créer la connexion à la base de données
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Récupérer le cabinet par défaut
        cabinet = db.query(Cabinet).filter(Cabinet.slug == "cabinet-principal").first()
        if not cabinet:
            print("❌ Aucun cabinet trouvé!")
            return
        
        print(f"✅ Cabinet trouvé: {cabinet.nom} (ID: {cabinet.id})")
        
        # Test 1: Email de test simple
        print("\n📧 Test 1: Envoi d'un email de test...")
        user = db.query(User).filter(User.cabinet_id == cabinet.id).first()
        if user:
            success = await email_service.send_email(
                to_email=user.email,
                subject="Test du système de notifications",
                template_name="test",
                template_data={
                    "user_name": user.full_name or user.username,
                    "message": "Si vous recevez cet email, le système de notifications fonctionne correctement!"
                }
            )
            if success:
                print(f"   ✅ Email envoyé à {user.email}")
            else:
                print(f"   ❌ Échec de l'envoi à {user.email}")
        
        # Test 2: Vérification des notifications automatiques
        print("\n🔍 Test 2: Vérification des notifications automatiques...")
        await NotificationService.check_and_send_notifications(db, cabinet.id)
        print("   ✅ Vérification terminée")
        
        # Test 3: Statistiques
        print("\n📊 Statistiques des notifications:")
        from app.models.notification import Notification
        from app.models.alerte import Alerte
        
        total_notifications = db.query(Notification).filter(
            Notification.cabinet_id == cabinet.id
        ).count()
        
        unread_notifications = db.query(Notification).filter(
            Notification.cabinet_id == cabinet.id,
            Notification.is_read == False
        ).count()
        
        total_alertes = db.query(Alerte).filter(
            Alerte.cabinet_id == cabinet.id
        ).count()
        
        active_alertes = db.query(Alerte).filter(
            Alerte.cabinet_id == cabinet.id,
            Alerte.active == True
        ).count()
        
        print(f"   - Notifications totales: {total_notifications}")
        print(f"   - Notifications non lues: {unread_notifications}")
        print(f"   - Alertes totales: {total_alertes}")
        print(f"   - Alertes actives: {active_alertes}")
        
        # Test 4: Configuration SMTP
        print("\n⚙️  Configuration SMTP:")
        print(f"   - Host: {settings.SMTP_HOST}")
        print(f"   - Port: {settings.SMTP_PORT}")
        print(f"   - From: {settings.SMTP_FROM_EMAIL}")
        print(f"   - TLS: {settings.SMTP_TLS}")
        print(f"   - SSL: {settings.SMTP_SSL}")
        
        if not settings.SMTP_USER:
            print("   ⚠️  ATTENTION: SMTP_USER non configuré dans .env")
        if not settings.SMTP_PASSWORD:
            print("   ⚠️  ATTENTION: SMTP_PASSWORD non configuré dans .env")
        
    except Exception as e:
        print(f"\n❌ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_notifications())