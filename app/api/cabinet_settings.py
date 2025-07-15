"""
API pour la gestion des paramètres du cabinet, incluant la localisation
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict

from app.core.deps import get_db, get_current_user, get_current_cabinet_id
from app.models import User, Cabinet
from app.core.validators import get_supported_countries, get_country_info, COUNTRY_CONFIGS
from app.schemas.cabinet import CabinetUpdate, CabinetResponse

router = APIRouter()


@router.get("/supported-countries", response_model=List[Dict])
async def get_all_supported_countries():
    """
    Retourne la liste de tous les pays supportés avec leurs configurations
    """
    countries = []
    for code, config in COUNTRY_CONFIGS.items():
        countries.append({
            "code": code,
            "name": config["name"],
            "currency": config["currency"],
            "currency_symbol": config.get("currency_symbol", config["currency"]),
            "company_id_name": config["company_id_name"],
            "phone_format": config["phone_format"],
            "date_format": config["date_format"],
            "iban_prefix": config["iban_prefix"]
        })
    
    # Trier par nom de pays
    countries.sort(key=lambda x: x["name"])
    
    return countries


@router.get("/country/{country_code}")
async def get_country_details(country_code: str):
    """
    Retourne les détails d'un pays spécifique
    """
    info = get_country_info(country_code.upper())
    if not info:
        raise HTTPException(status_code=404, detail="Pays non supporté")
    
    return {
        "code": country_code.upper(),
        **info
    }


@router.get("/settings", response_model=CabinetResponse)
async def get_cabinet_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    cabinet_id: int = Depends(get_current_cabinet_id)
):
    """
    Récupère les paramètres du cabinet incluant la localisation
    """
    cabinet = db.query(Cabinet).filter(Cabinet.id == cabinet_id).first()
    if not cabinet:
        raise HTTPException(status_code=404, detail="Cabinet non trouvé")
    
    return cabinet


@router.put("/settings", response_model=CabinetResponse)
async def update_cabinet_settings(
    cabinet_update: CabinetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    cabinet_id: int = Depends(get_current_cabinet_id)
):
    """
    Met à jour les paramètres du cabinet
    Seuls les administrateurs peuvent modifier ces paramètres
    """
    # Vérifier que l'utilisateur est admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403, 
            detail="Seuls les administrateurs peuvent modifier les paramètres du cabinet"
        )
    
    # Récupérer le cabinet
    cabinet = db.query(Cabinet).filter(Cabinet.id == cabinet_id).first()
    if not cabinet:
        raise HTTPException(status_code=404, detail="Cabinet non trouvé")
    
    # Valider le code pays si fourni
    if cabinet_update.pays_code:
        if cabinet_update.pays_code not in COUNTRY_CONFIGS:
            raise HTTPException(
                status_code=400,
                detail=f"Code pays invalide: {cabinet_update.pays_code}"
            )
        
        # Mettre à jour automatiquement les champs liés
        country_info = get_country_info(cabinet_update.pays_code)
        cabinet.devise = country_info["currency"]
        cabinet.format_date = country_info["date_format"]
    
    # Mettre à jour les champs fournis
    update_data = cabinet_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(cabinet, field, value)
    
    db.commit()
    db.refresh(cabinet)
    
    return cabinet


@router.get("/timezones")
async def get_supported_timezones():
    """
    Retourne la liste des fuseaux horaires supportés
    """
    # Fuseaux horaires principaux pour les pays supportés
    timezones = {
        "Europe/Paris": "France, Europe de l'Ouest",
        "Africa/Douala": "Cameroun, Gabon, Tchad, RCA, Guinée Équatoriale",
        "Africa/Dakar": "Sénégal, Mali, Mauritanie",
        "Africa/Abidjan": "Côte d'Ivoire, Burkina Faso, Togo, Bénin, Niger, Guinée-Bissau",
        "Africa/Brazzaville": "Congo-Brazzaville",
        "Indian/Comoro": "Comores"
    }
    
    return [
        {"value": tz, "label": f"{tz} ({desc})"}
        for tz, desc in timezones.items()
    ]


@router.get("/languages")
async def get_supported_languages():
    """
    Retourne la liste des langues supportées
    """
    languages = [
        {"code": "fr-FR", "name": "Français (France)"},
        {"code": "fr-CM", "name": "Français (Cameroun)"},
        {"code": "fr-SN", "name": "Français (Sénégal)"},
        {"code": "fr-CI", "name": "Français (Côte d'Ivoire)"},
        {"code": "fr-BF", "name": "Français (Burkina Faso)"},
        {"code": "fr-ML", "name": "Français (Mali)"},
        {"code": "fr-TG", "name": "Français (Togo)"},
        {"code": "fr-BJ", "name": "Français (Bénin)"},
        {"code": "fr-GA", "name": "Français (Gabon)"},
        {"code": "fr-CG", "name": "Français (Congo)"},
        {"code": "fr-TD", "name": "Français (Tchad)"},
        {"code": "fr-CF", "name": "Français (RCA)"},
        {"code": "fr-GQ", "name": "Français (Guinée Équatoriale)"},
        {"code": "fr-NE", "name": "Français (Niger)"},
        {"code": "fr-GW", "name": "Français (Guinée-Bissau)"},
        {"code": "fr-KM", "name": "Français (Comores)"}
    ]
    
    return languages