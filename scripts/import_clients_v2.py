#!/usr/bin/env python3
"""
Script d'import des clients avec nom, forme juridique et SIRET
"""
import os
import sys
from pathlib import Path

# Ajouter le répertoire parent au path Python
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.client import Client


# Liste des clients à importer
CLIENTS_DATA = [
    {"nom": "AIT BENALI", "forme_juridique": "SARL", "siret": "45107545100042"},
    {"nom": "A.M.K", "forme_juridique": "SARL", "siret": "82329803900012"},
    {"nom": "ASIAN PALACE", "forme_juridique": "SARL", "siret": "50960136500018"},
    {"nom": "ASIAN SARI CENTER", "forme_juridique": "SARL", "siret": "42317519900011"},
    {"nom": "AUGUSTO", "forme_juridique": "SARL", "siret": ""},
    {"nom": "AZEROUAL Lahcen", "forme_juridique": "EI", "siret": "81477405500010"},
    {"nom": "B&B TRANSPORTS", "forme_juridique": "SARL", "siret": "50437983500011"},
    {"nom": "BA RENOV", "forme_juridique": "SARL", "siret": "50513857800024"},
    {"nom": "BATIMENT ASSISTANCE", "forme_juridique": "SASU", "siret": "82803598000022"},
    {"nom": "BENSAFIR Brahim", "forme_juridique": "EI", "siret": "39307987600016"},
    {"nom": "BENSSI", "forme_juridique": "EI", "siret": "34439441600012"},
    {"nom": "CRETTEDISTRI", "forme_juridique": "SASU", "siret": "75243058700010"},
    {"nom": "DABACHINE Mohamed", "forme_juridique": "EI", "siret": "38769028200026"},
    {"nom": "DAFIR NASRIA", "forme_juridique": "EI", "siret": "79458894700018"},
    {"nom": "DANA Coiffure", "forme_juridique": "SASU", "siret": "84121359800011"},
    {"nom": "DJAH", "forme_juridique": "SARL", "siret": "43490215100019"},
    {"nom": "ELMOUTAWAKIL ABDELLAH", "forme_juridique": "EI", "siret": "34400779400011"},
    {"nom": "E-TINCEL", "forme_juridique": "SAS", "siret": "92136864300018"},
    {"nom": "EURINOX", "forme_juridique": "SARL", "siret": "52918265100024"},
    {"nom": "FLEUR D'EDEN", "forme_juridique": "SARL", "siret": "80096075900028"},
    {"nom": "FSR DECOR", "forme_juridique": "SARL", "siret": "84352030500015"},
    {"nom": "HAKOUTI Jamel", "forme_juridique": "EI", "siret": "81268098100014"},
    {"nom": "HAKOUTI Rachid", "forme_juridique": "EI", "siret": "44411999400010"},
    {"nom": "HKH TRANSPORT", "forme_juridique": "SARL", "siret": "79980500700041"},
    {"nom": "HOTEL CESAR", "forme_juridique": "EURL", "siret": "43970871000041"},
    {"nom": "HUBERT PÈRE ET FILS", "forme_juridique": "SASU", "siret": "87884413300016"},
    {"nom": "IGUDI", "forme_juridique": "SARL", "siret": "43141377200028"},
    {"nom": "IDF ECO RENOV", "forme_juridique": "EURL", "siret": "75233603200038"},
    {"nom": "IKORINE", "forme_juridique": "SARL", "siret": "49960352000010"},
    {"nom": "JAZZ COFFEE", "forme_juridique": "SASU", "siret": "80940409800018"},
    {"nom": "LE BISTRO DU MARCHE", "forme_juridique": "SASU", "siret": "91015433500012"},
    {"nom": "LE CARREFOUR", "forme_juridique": "SARL", "siret": "52788205400010"},
    {"nom": "LE MATANA", "forme_juridique": "SASU", "siret": "89955405900019"},
    {"nom": "LES MAITRES BATISSEURS", "forme_juridique": "SASU", "siret": "82879259800017"},
    {"nom": "LES SAVEURS DE TUNIS", "forme_juridique": "SARL", "siret": "80527888400012"},
    {"nom": "MAELYS", "forme_juridique": "SAS", "siret": "83868634300016"},
    {"nom": "MAISON PERRIER", "forme_juridique": "SARL", "siret": "82187138100017"},
    {"nom": "MISATO", "forme_juridique": "SARL", "siret": "81815397500029"},
    {"nom": "MRJ", "forme_juridique": "SASU", "siret": "83487314300012"},
    {"nom": "MY", "forme_juridique": "SARL", "siret": "44022381600016"},
    {"nom": "NAFYBI", "forme_juridique": "SNC", "siret": "79411003100018"},
    {"nom": "NEW INDIA", "forme_juridique": "SARL", "siret": "42332398900024"},
    {"nom": "NOUR", "forme_juridique": "SARL", "siret": "49480467700024"},
    {"nom": "O HANOUT", "forme_juridique": "SARL", "siret": "80861609800022"},
    {"nom": "OUARHOUS SAID", "forme_juridique": "EI", "siret": "32631186700039"},
    {"nom": "OULYOU", "forme_juridique": "SARL", "siret": "52923695200014"},
    {"nom": "PALMERAIE", "forme_juridique": "SARL", "siret": "83429868900011"},
    {"nom": "PEINTURE IDF", "forme_juridique": "SARL", "siret": "90169969400013"},
    {"nom": "PRIVATE CAB", "forme_juridique": "SASU", "siret": "80145467900011"},
    {"nom": "RNS", "forme_juridique": "SASU", "siret": "85362864200011"},
    {"nom": "SABIRI LAHCEN (Loueur de Fonds)", "forme_juridique": "EI", "siret": "34823452700011"},
    {"nom": "SIMONNET Gilles", "forme_juridique": "EI", "siret": "38106129000023"},
    {"nom": "SPRINT SECURITE", "forme_juridique": "SAS", "siret": "89802637200018"},
    {"nom": "TAMACHT", "forme_juridique": "SARL", "siret": "48057881400018"},
    {"nom": "TAIM PIZZA", "forme_juridique": "SARL", "siret": "75095189900012"},
    {"nom": "TERCHOUNE Abdelhakim", "forme_juridique": "EI", "siret": "48812900800014"},
    {"nom": "THE ACCESS HOUSE", "forme_juridique": "EURL", "siret": "75089649000018"},
    {"nom": "TROP TOP", "forme_juridique": "SARL", "siret": "50442184300013"},
    {"nom": "VSP FACILITIES", "forme_juridique": "SAS", "siret": "92989684300018"},
    {"nom": "VSP (Vigilante Sécurité Privée)", "forme_juridique": "SARL", "siret": "79014819100055"},
]


def import_clients():
    """Importe les clients dans la base de données"""
    db = SessionLocal()
    
    try:
        # Supprimer tous les clients existants
        deleted = db.query(Client).delete()
        print(f"Supprimé {deleted} clients existants")
        
        # Importer les nouveaux clients
        for i, client_data in enumerate(CLIENTS_DATA, 1):
            # Générer un numéro client unique
            numero_client = f"CLI{i:05d}"
            
            # Extraire le nom du gérant pour les EI
            nom_gerant = None
            if client_data["forme_juridique"] == "EI":
                # Pour les EI, le nom du client est souvent le nom du gérant
                nom_gerant = client_data["nom"]
            
            client = Client(
                nom=client_data["nom"],
                numero_client=numero_client,
                forme_juridique=client_data["forme_juridique"],
                siret=client_data["siret"] if client_data["siret"] else None,
                nom_gerant=nom_gerant,
                # Les autres champs seront remplis depuis le frontend
                telephone=None,
                email=None,
                adresse=None,
                ville=None,
                code_postal=None,
                telephone_gerant=None,
                email_gerant=None,
                is_active=True
            )
            db.add(client)
            print(f"Ajouté: {client.nom} ({client.forme_juridique}) - {client.numero_client}")
        
        # Commit des changements
        db.commit()
        print(f"\n{len(CLIENTS_DATA)} clients importés avec succès!")
        
    except Exception as e:
        db.rollback()
        print(f"Erreur lors de l'import: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    import_clients()