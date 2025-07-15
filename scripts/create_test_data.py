#!/usr/bin/env python3
"""
Script pour créer des données de test
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, date, timedelta
import random
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.user import User
from app.models.client import Client
from app.models.dossier import Dossier, StatusDossier, TypeDossier
from app.models.alerte import Alerte, TypeAlerte, NiveauAlerte
from app.models.historique import HistoriqueDossier

# Créer les tables si elles n'existent pas
Base.metadata.create_all(bind=engine)

def create_test_data():
    db = SessionLocal()
    
    try:
        print("🧹 Nettoyage des données existantes...")
        # Nettoyer les tables dans le bon ordre (contraintes FK)
        db.query(HistoriqueDossier).delete()
        db.query(Alerte).delete()
        db.query(Dossier).delete()
        db.query(Client).delete()
        db.query(User).delete()
        db.commit()
        
        print("👥 Création des utilisateurs...")
        users = [
            User(
                username="admin",
                email="admin@cabinet.com",
                full_name="Administrateur Principal",
                hashed_password=get_password_hash("admin123"),
                role="admin",
                is_active=True
            ),
            User(
                username="manager",
                email="manager@cabinet.com",
                full_name="Sophie Martin",
                hashed_password=get_password_hash("manager123"),
                role="manager",
                is_active=True
            ),
            User(
                username="comptable1",
                email="comptable1@cabinet.com",
                full_name="Jean Dupont",
                hashed_password=get_password_hash("comptable123"),
                role="collaborateur",
                is_active=True
            ),
            User(
                username="comptable2",
                email="comptable2@cabinet.com",
                full_name="Marie Durand",
                hashed_password=get_password_hash("comptable123"),
                role="collaborateur",
                is_active=True
            )
        ]
        
        for user in users:
            db.add(user)
        db.commit()
        print(f"✅ {len(users)} utilisateurs créés")
        
        print("🏢 Création des clients...")
        clients = [
            Client(
                nom="Boulangerie Moderne",
                numero_client="CLI001",
                email="contact@boulangeriemoderne.fr",
                telephone="01 23 45 67 89",
                adresse="12 rue du Pain",
                ville="Paris",
                code_postal="75001",
                siret="12345678900001"
            ),
            Client(
                nom="Tech Solutions SARL",
                numero_client="CLI002",
                email="info@techsolutions.fr",
                telephone="01 98 76 54 32",
                adresse="45 avenue de l'Innovation",
                ville="Lyon",
                code_postal="69001",
                siret="98765432100001"
            ),
            Client(
                nom="Restaurant Le Gourmet",
                numero_client="CLI003",
                email="contact@legourmet.fr",
                telephone="04 12 34 56 78",
                adresse="8 place de la République",
                ville="Marseille",
                code_postal="13001",
                siret="11223344556677"
            ),
            Client(
                nom="Garage Auto Plus",
                numero_client="CLI004",
                email="garage@autoplus.fr",
                telephone="05 11 22 33 44",
                adresse="Zone industrielle Nord",
                ville="Toulouse",
                code_postal="31000",
                siret="99887766554433"
            ),
            Client(
                nom="Cabinet Médical Santé",
                numero_client="CLI005",
                email="secretariat@cabmed.fr",
                telephone="03 55 44 33 22",
                adresse="15 rue de la Santé",
                ville="Strasbourg",
                code_postal="67000",
                siret="55443322110099"
            )
        ]
        
        for client in clients:
            db.add(client)
        db.commit()
        print(f"✅ {len(clients)} clients créés")
        
        print("📁 Création des dossiers...")
        # Récupérer les IDs
        comptable1 = db.query(User).filter(User.username == "comptable1").first()
        comptable2 = db.query(User).filter(User.username == "comptable2").first()
        clients_db = db.query(Client).all()
        
        dossiers = []
        today = date.today()
        
        # Créer des dossiers avec différents statuts
        scenarios = [
            # Dossiers en retard
            {
                "client": clients_db[0],
                "type": TypeDossier.TVA,
                "status": StatusDossier.EN_COURS,
                "deadline": today - timedelta(days=5),
                "responsable": comptable1,
                "description": "Déclaration TVA mensuelle - URGENT"
            },
            {
                "client": clients_db[1],
                "type": TypeDossier.BILAN,
                "status": StatusDossier.EN_ATTENTE,
                "deadline": today - timedelta(days=2),
                "responsable": comptable2,
                "description": "Bilan annuel 2024 - Documents manquants"
            },
            # Dossiers à échéance proche
            {
                "client": clients_db[2],
                "type": TypeDossier.TVA,
                "status": StatusDossier.EN_COURS,
                "deadline": today + timedelta(days=2),
                "responsable": comptable1,
                "description": "Déclaration TVA trimestrielle"
            },
            {
                "client": clients_db[3],
                "type": TypeDossier.SOCIAL,
                "status": StatusDossier.EN_COURS,
                "deadline": today + timedelta(days=3),
                "responsable": comptable2,
                "description": "Déclarations sociales mensuelles"
            },
            # Dossiers normaux
            {
                "client": clients_db[4],
                "type": TypeDossier.FISCAL,
                "status": StatusDossier.NOUVEAU,
                "deadline": today + timedelta(days=15),
                "responsable": comptable1,
                "description": "Liasse fiscale 2024"
            },
            {
                "client": clients_db[0],
                "type": TypeDossier.SOCIAL,
                "status": StatusDossier.EN_COURS,
                "deadline": today + timedelta(days=10),
                "responsable": comptable2,
                "description": "Fiches de paie décembre"
            },
            # Dossiers complétés
            {
                "client": clients_db[1],
                "type": TypeDossier.TVA,
                "status": StatusDossier.COMPLETE,
                "deadline": today - timedelta(days=10),
                "responsable": comptable1,
                "description": "TVA novembre - Complété",
                "completed_at": today - timedelta(days=8)
            },
            {
                "client": clients_db[2],
                "type": TypeDossier.AUTRE,
                "status": StatusDossier.COMPLETE,
                "deadline": today - timedelta(days=20),
                "responsable": comptable2,
                "description": "Audit interne - Terminé",
                "completed_at": today - timedelta(days=15)
            }
        ]
        
        for scenario in scenarios:
            dossier = Dossier(
                client_id=scenario["client"].id,
                client_name=scenario["client"].nom,
                type_dossier=scenario["type"],
                status=scenario["status"],
                deadline=scenario["deadline"],
                responsable_id=scenario["responsable"].id,
                description=scenario["description"],
                priorite=2 if scenario["deadline"] < today else (1 if scenario["deadline"] < today + timedelta(days=3) else 0)
            )
            if "completed_at" in scenario:
                dossier.completed_at = scenario["completed_at"]
            
            db.add(dossier)
            dossiers.append(dossier)
        
        db.commit()
        print(f"✅ {len(dossiers)} dossiers créés")
        
        print("🚨 Création des alertes...")
        # Créer des alertes pour les dossiers en retard ou urgents
        alertes_count = 0
        for dossier in dossiers:
            if dossier.deadline < today and dossier.status != StatusDossier.COMPLETE:
                jours_retard = (today - dossier.deadline).days
                alerte = Alerte(
                    dossier_id=dossier.id,
                    type_alerte=TypeAlerte.RETARD,
                    niveau=NiveauAlerte.URGENT if jours_retard > 3 else NiveauAlerte.WARNING,
                    message=f"Retard de {jours_retard} jours sur le dossier {dossier.client_name}",
                    active=True
                )
                db.add(alerte)
                alertes_count += 1
            elif dossier.deadline <= today + timedelta(days=3) and dossier.status not in [StatusDossier.COMPLETE, StatusDossier.ARCHIVE]:
                alerte = Alerte(
                    dossier_id=dossier.id,
                    type_alerte=TypeAlerte.DEADLINE_PROCHE,
                    niveau=NiveauAlerte.WARNING,
                    message=f"Échéance dans {(dossier.deadline - today).days} jours pour {dossier.client_name}",
                    active=True
                )
                db.add(alerte)
                alertes_count += 1
        
        db.commit()
        print(f"✅ {alertes_count} alertes créées")
        
        print("📝 Création de l'historique...")
        # Ajouter quelques entrées d'historique
        for dossier in dossiers[:3]:
            hist = HistoriqueDossier(
                dossier_id=dossier.id,
                user_id=dossier.responsable_id,
                action="creation",
                new_value=dossier.status.value,
                commentaire="Dossier créé"
            )
            db.add(hist)
        
        db.commit()
        print("✅ Historique créé")
        
        print("\n🎉 Données de test créées avec succès!")
        print("\n📊 Résumé:")
        print(f"  - Utilisateurs: {len(users)}")
        print(f"  - Clients: {len(clients)}")
        print(f"  - Dossiers: {len(dossiers)}")
        print(f"  - Alertes: {alertes_count}")
        
        print("\n🔐 Identifiants de connexion:")
        print("  Admin    : admin / admin123")
        print("  Manager  : manager / manager123")
        print("  Comptable: comptable1 / comptable123")
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_data()