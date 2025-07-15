#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta, date
import random
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.dossier import Dossier, TypeDossier, StatusDossier, PrioriteDossier
from app.models.user import User

# Liste des clients avec leurs informations
CLIENTS = [
    ("AIT BENALI", "SARL", "45107545100042"),
    ("A.M.K", "SARL", "82329803900012"),
    ("ASIAN PALACE", "SARL", "50960136500018"),
    ("ASIAN SARI CENTER", "SARL", "42317519900011"),
    ("AUGUSTO", "SARL", ""),
    ("AZEROUAL Lahcen", "EI", "81477405500010"),
    ("B&B TRANSPORTS", "SARL", "50437983500011"),
    ("BA RENOV", "SARL", "50513857800024"),
    ("BATIMENT ASSISTANCE", "SASU", "82803598000022"),
    ("BENSAFIR Brahim", "EI", "39307987600016"),
    ("BENSSI", "EI", "34439441600012"),
    ("CRETTEDISTRI", "SASU", "75243058700010"),
    ("DABACHINE Mohamed", "EI", "38769028200026"),
    ("DAFIR NASRIA", "EI", "79458894700018"),
    ("DANA Coiffure", "SASU", "84121359800011"),
    ("DJAH", "SARL", "43490215100019"),
    ("ELMOUTAWAKIL ABDELLAH", "EI", "34400779400011"),
    ("E-TINCEL", "SAS", "92136864300018"),
    ("EURINOX", "SARL", "52918265100024"),
    ("FLEUR D'EDEN", "SARL", "80096075900028"),
    ("FSR DECOR", "SARL", "84352030500015"),
    ("HAKOUTI Jamel", "EI", "81268098100014"),
    ("HAKOUTI Rachid", "EI", "44411999400010"),
    ("HKH TRANSPORT", "SARL", "79980500700041"),
    ("HOTEL CESAR", "EURL", "43970871000041"),
    ("HUBERT PÈRE ET FILS", "SASU", "87884413300016"),
    ("IGUDI", "SARL", "43141377200028"),
    ("IDF ECO RENOV", "EURL", "75233603200038"),
    ("IKORINE", "SARL", "49960352000010"),
    ("JAZZ COFFEE", "SASU", "80940409800018"),
    ("LE BISTRO DU MARCHE", "SASU", "91015433500012"),
    ("LE CARREFOUR", "SARL", "52788205400010"),
    ("LE MATANA", "SASU", "89955405900019"),
    ("LES MAITRES BATISSEURS", "SASU", "82879259800017"),
    ("LES SAVEURS DE TUNIS", "SARL", "80527888400012"),
    ("MAELYS", "SAS", "83868634300016"),
    ("MAISON PERRIER", "SARL", "82187138100017"),
    ("MISATO", "SARL", "81815397500029"),
    ("MRJ", "SASU", "83487314300012"),
    ("MY", "SARL", "44022381600016"),
    ("NAFYBI", "SNC", "79411003100018"),
    ("NEW INDIA", "SARL", "42332398900024"),
    ("NOUR", "SARL", "49480467700024"),
    ("O HANOUT", "SARL", "80861609800022"),
    ("OUARHOUS SAID", "EI", "32631186700039"),
    ("OULYOU", "SARL", "52923695200014"),
    ("PALMERAIE", "SARL", "83429868900011"),
    ("PEINTURE IDF", "SARL", "90169969400013"),
    ("PRIVATE CAB", "SASU", "80145467900011"),
    ("RNS", "SASU", "85362864200011"),
    ("SABIRI LAHCEN (Loueur de Fonds)", "EI", "34823452700011"),
    ("SIMONNET Gilles", "EI", "38106129000023"),
    ("SPRINT SECURITE", "SAS", "89802637200018"),
    ("TAMACHT", "SARL", "48057881400018"),
    ("TAIM PIZZA", "SARL", "75095189900012"),
    ("TERCHOUNE Abdelhakim", "EI", "48812900800014"),
    ("THE ACCESS HOUSE", "EURL", "75089649000018"),
    ("TROP TOP", "SARL", "50442184300013"),
    ("VSP FACILITIES", "SAS", "92989684300018"),
    ("VSP (Vigilante Sécurité Privée )", "SARL", "79014819100055"),
]

def create_dossiers_for_clients():
    db = SessionLocal()
    try:
        # Récupérer le premier utilisateur (pour l'association)
        user = db.query(User).first()
        if not user:
            print("❌ Aucun utilisateur trouvé. Créez d'abord un utilisateur.")
            return
        
        print(f"👤 Utilisation de l'utilisateur: {user.username}")
        
        # Types de services disponibles
        services_disponibles = ["COMPTABILITE", "TVA", "PAIE", "JURIDIQUE", "LIASSE_FISCALE", "CREATION_ENTREPRISE"]
        
        # Périodes comptables
        periodes = ["Mensuel", "Trimestriel", "Annuel"]
        exercices = ["2023", "2024"]
        
        dossiers_crees = 0
        
        for nom_client, forme_juridique, siret in CLIENTS:
            # Déterminer les services selon le type d'entreprise
            if forme_juridique == "EI":
                # Entrepreneur individuel - services de base
                services = random.sample(["COMPTABILITE", "TVA"], k=random.randint(1, 2))
            elif forme_juridique in ["SARL", "SAS", "SASU", "EURL"]:
                # Sociétés - plus de services
                services = random.sample(services_disponibles[:-1], k=random.randint(2, 4))
            else:  # SNC
                services = random.sample(services_disponibles, k=random.randint(1, 3))
            
            # Créer plusieurs dossiers par client (différentes périodes/types)
            nb_dossiers = random.randint(1, 4)
            
            for i in range(nb_dossiers):
                # Choisir le type principal
                type_principal = random.choice(services)
                
                # Déterminer la période et l'exercice
                if type_principal == "LIASSE_FISCALE":
                    periode = "Annuel"
                    exercice = random.choice(exercices)
                    description = f"Liasse fiscale {exercice}"
                elif type_principal == "TVA":
                    periode = random.choice(["Mensuel", "Trimestriel"])
                    mois = random.randint(1, 12)
                    description = f"TVA {periode} - {mois:02d}/2024"
                elif type_principal == "PAIE":
                    periode = "Mensuel"
                    mois = random.randint(1, 12)
                    description = f"Paie {mois:02d}/2024"
                else:
                    periode = random.choice(periodes)
                    exercice = random.choice(exercices)
                    description = f"{type_principal.replace('_', ' ').title()} {periode} {exercice}"
                
                # Générer les dates
                today = date.today()
                
                # Date d'échéance aléatoire
                if random.random() < 0.3:  # 30% en retard
                    date_echeance = today - timedelta(days=random.randint(1, 30))
                    statut = StatusDossier.EN_COURS
                elif random.random() < 0.5:  # 20% urgents
                    date_echeance = today + timedelta(days=random.randint(1, 7))
                    statut = StatusDossier.EN_COURS
                else:  # 50% normaux
                    date_echeance = today + timedelta(days=random.randint(8, 60))
                    statut = random.choice([StatusDossier.NOUVEAU, StatusDossier.EN_COURS])
                
                # Quelques dossiers complétés
                if random.random() < 0.2:
                    statut = StatusDossier.COMPLETE
                    completed_at = today - timedelta(days=random.randint(1, 30))
                else:
                    completed_at = None
                
                # Priorité
                if date_echeance < today:
                    priorite = PrioriteDossier.URGENTE
                elif date_echeance <= today + timedelta(days=7):
                    priorite = random.choice([PrioriteDossier.HAUTE, PrioriteDossier.URGENTE])
                else:
                    priorite = random.choice([PrioriteDossier.NORMALE, PrioriteDossier.BASSE])
                
                # Générer une référence unique
                ref_num = dossiers_crees + 1
                reference = f"{exercice if 'exercice' in locals() else '2024'}-{type_principal[:3]}-{ref_num:04d}"
                
                # Créer le dossier
                dossier = Dossier(
                    reference=reference,
                    nom_client=nom_client,
                    type_entreprise=forme_juridique,
                    numero_siret=siret if siret else None,
                    type_dossier=type_principal,
                    services=services,
                    periode_comptable=periode,
                    exercice_fiscal=exercice if "exercice" in locals() else "2024",
                    date_echeance=date_echeance,
                    statut=statut,
                    priorite=priorite,
                    description=description,
                    notes=f"Client depuis {random.randint(1, 10)} ans" if random.random() < 0.5 else None,
                    contact_client=f"contact@{nom_client.lower().replace(' ', '').replace('&', 'et')}.fr",
                    telephone_client=f"01{random.randint(10, 99)}{random.randint(10, 99)}{random.randint(10, 99)}{random.randint(10, 99)}",
                    user_id=user.id,
                    completed_at=completed_at
                )
                
                db.add(dossier)
                dossiers_crees += 1
        
        db.commit()
        print(f"✅ {dossiers_crees} dossiers créés pour {len(CLIENTS)} clients")
        
        # Afficher les statistiques
        stats = {
            "total": db.query(Dossier).count(),
            "en_retard": db.query(Dossier).filter(
                Dossier.date_echeance < today,
                Dossier.statut != StatusDossier.COMPLETE
            ).count(),
            "urgents": db.query(Dossier).filter(
                Dossier.priorite == PrioriteDossier.URGENTE
            ).count(),
            "completes": db.query(Dossier).filter(
                Dossier.statut == StatusDossier.COMPLETE
            ).count(),
        }
        
        print("\n📊 Statistiques des dossiers:")
        print(f"   - Total: {stats['total']}")
        print(f"   - En retard: {stats['en_retard']}")
        print(f"   - Urgents: {stats['urgents']}")
        print(f"   - Complétés: {stats['completes']}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_dossiers_for_clients()