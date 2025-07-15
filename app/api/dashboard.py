from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
from datetime import datetime, date, timedelta

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_cabinet_id
from app.core.cache import cache_dashboard, invalidate_cache
from app.models.user import User
from app.models.dossier import Dossier, StatusDossier, PrioriteDossier
from app.models.echeance import Echeance

router = APIRouter()


@router.get("/stats")
@cache_dashboard
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    cabinet_id: int = Depends(get_current_cabinet_id),
    db: Session = Depends(get_db),
    period: str = None
):
    """Récupérer les statistiques pour le tableau de bord"""
    today = date.today()
    
    # Déterminer la date de début selon la période
    if period == 'today':
        start_date = today
    elif period == 'week':
        start_date = today - timedelta(days=7)
    elif period == 'month':
        start_date = today - timedelta(days=30)
    elif period == 'quarter':
        start_date = today - timedelta(days=90)
    elif period == 'year':
        start_date = today - timedelta(days=365)
    else:
        start_date = None
    
    # Compter les dossiers en retard (date_echeance dépassée et statut non complété)
    query_retard = db.query(func.count(Dossier.id)).filter(
        and_(
            Dossier.date_echeance < today,
            Dossier.statut != StatusDossier.COMPLETE,
            Dossier.statut != StatusDossier.ARCHIVE
        )
    )
    if start_date:
        query_retard = query_retard.filter(Dossier.created_at >= start_date)
    dossiers_en_retard = query_retard.scalar() or 0
    
    # Compter les dossiers avec échéance aujourd'hui
    query_aujourdhui = db.query(func.count(Dossier.id)).filter(
        and_(
            Dossier.date_echeance == today,
            Dossier.statut != StatusDossier.COMPLETE,
            Dossier.statut != StatusDossier.ARCHIVE
        )
    )
    if start_date:
        query_aujourdhui = query_aujourdhui.filter(Dossier.created_at >= start_date)
    dossiers_aujourdhui = query_aujourdhui.scalar() or 0
    
    # Compter les dossiers urgents (priorité URGENTE)
    query_urgents = db.query(func.count(Dossier.id)).filter(
        and_(
            Dossier.priorite == PrioriteDossier.URGENTE,
            Dossier.statut != StatusDossier.COMPLETE,
            Dossier.statut != StatusDossier.ARCHIVE
        )
    )
    if start_date:
        query_urgents = query_urgents.filter(Dossier.created_at >= start_date)
    dossiers_urgents = query_urgents.scalar() or 0
    
    # Compter les dossiers complétés dans la période
    if period == 'today':
        periode_complete = today
    elif period == 'week':
        periode_complete = today - timedelta(days=7)
    elif period == 'month' or not period:
        periode_complete = date(today.year, today.month, 1)
    elif period == 'quarter':
        periode_complete = today - timedelta(days=90)
    elif period == 'year':
        periode_complete = date(today.year, 1, 1)
    else:
        periode_complete = date(today.year, today.month, 1)
        
    dossiers_completes = db.query(func.count(Dossier.id)).filter(
        and_(
            Dossier.statut == StatusDossier.COMPLETE,
            Dossier.completed_at >= periode_complete
        )
    ).scalar() or 0
    
    return {
        "en_retard": dossiers_en_retard,
        "aujourdhui": dossiers_aujourdhui,
        "urgents": dossiers_urgents,
        "completes": dossiers_completes
    }


@router.get("/dossiers-retard")
async def get_dossiers_en_retard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    period: str = None
):
    """Récupérer les dossiers avec échéances en retard"""
    today = date.today()
    
    # Récupérer les échéances en retard avec les infos du dossier
    query = db.query(Echeance, Dossier).join(
        Dossier, Echeance.dossier_id == Dossier.id
    ).filter(
        and_(
            Echeance.date_echeance < today,
            Echeance.statut != 'COMPLETE',
            Dossier.statut != StatusDossier.ARCHIVE
        )
    )
    
    # Grouper par dossier et prendre l'échéance la plus ancienne en retard
    echeances_retard = query.order_by(Echeance.date_echeance).all()
    
    # Regrouper par dossier (prendre la première échéance en retard de chaque dossier)
    dossiers_vus = set()
    result = []
    
    for echeance, dossier in echeances_retard:
        if dossier.id not in dossiers_vus and len(result) < 5:
            dossiers_vus.add(dossier.id)
            jours_retard = (today - echeance.date_echeance).days
            result.append({
                "id": dossier.id,
                "nom_client": dossier.nom_client,
                "type_dossier": dossier.type_dossier,
                "date_echeance": echeance.date_echeance.isoformat(),
                "jours_retard": jours_retard,
                "priorite": dossier.priorite
            })
    
    return result


@router.get("/alertes-urgentes")
async def get_alertes_urgentes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    period: str = None
):
    """Récupérer les alertes urgentes basées sur les échéances"""
    today = date.today()
    prochains_jours = today + timedelta(days=3)
    
    alertes = []
    
    # Échéances en retard de plus de 3 jours
    query_retard = db.query(Echeance, Dossier).join(
        Dossier, Echeance.dossier_id == Dossier.id
    ).filter(
        and_(
            Echeance.date_echeance < today - timedelta(days=3),
            Echeance.statut != 'COMPLETE',
            Dossier.statut != StatusDossier.ARCHIVE
        )
    ).order_by(Echeance.date_echeance).limit(3).all()
    
    for echeance, dossier in query_retard:
        jours_retard = (today - echeance.date_echeance).days
        alertes.append({
            "id": dossier.id,
            "type": "retard",
            "message": f"Retard de {jours_retard} jours - {echeance.periode_label}",
            "client": dossier.nom_client,
            "niveau": "urgent"
        })
    
    # Échéances dans les 3 prochains jours
    query_proche = db.query(Echeance, Dossier).join(
        Dossier, Echeance.dossier_id == Dossier.id
    ).filter(
        and_(
            Echeance.date_echeance >= today,
            Echeance.date_echeance <= prochains_jours,
            Echeance.statut != 'COMPLETE',
            Dossier.statut != StatusDossier.ARCHIVE
        )
    ).order_by(Echeance.date_echeance).limit(3).all()
    
    for echeance, dossier in query_proche:
        jours_restants = (echeance.date_echeance - today).days
        alertes.append({
            "id": dossier.id,
            "type": "echeance",
            "message": f"Échéance dans {jours_restants} jour{'s' if jours_restants > 1 else ''} - {echeance.periode_label}",
            "client": dossier.nom_client,
            "niveau": "warning"
        })
    
    return alertes[:5]  # Limiter à 5 alertes


@router.get("/trends")
async def get_trends_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    period: str = "month"  # month, week, year
):
    """Récupérer les données de tendances pour les graphiques"""
    import logging
    logger = logging.getLogger(__name__)
    
    today = date.today()
    logger.info(f"Trends API appelée avec period={period}")
    
    if period == "month":
        # Données des 30 derniers jours
        start_date = today - timedelta(days=30)
        days = 30
    elif period == "week":
        # Données des 7 derniers jours
        start_date = today - timedelta(days=7)
        days = 7
    else:  # year
        # Données des 12 derniers mois
        start_date = today - timedelta(days=365)
        days = 365
    
    # Récupérer les données pour chaque jour/mois
    data = []
    
    if period in ["month", "week"]:
        # Données quotidiennes
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            
            # Échéances créées ce jour
            created = db.query(func.count(Echeance.id)).filter(
                func.date(Echeance.created_at) == current_date
            ).scalar() or 0
            
            # Échéances complétées ce jour
            completed = db.query(func.count(Echeance.id)).filter(
                and_(
                    func.date(Echeance.updated_at) == current_date,
                    Echeance.statut == 'COMPLETE'
                )
            ).scalar() or 0
            
            # Échéances en retard à la fin de ce jour
            overdue = db.query(func.count(Echeance.id)).filter(
                and_(
                    Echeance.date_echeance <= current_date,
                    Echeance.statut != 'COMPLETE',
                    Echeance.created_at <= current_date + timedelta(days=1)
                )
            ).scalar() or 0
            
            data.append({
                "date": current_date.strftime("%d/%m"),
                "created": created,
                "completed": completed,
                "overdue": overdue
            })
    else:
        # Données mensuelles pour l'année
        for i in range(12):
            month_date = today - timedelta(days=30 * (11 - i))
            month = month_date.month
            year = month_date.year
            
            # Dossiers créés ce mois
            created = db.query(func.count(Dossier.id)).filter(
                and_(
                    extract('month', Dossier.created_at) == month,
                    extract('year', Dossier.created_at) == year
                )
            ).scalar() or 0
            
            # Dossiers complétés ce mois
            completed = db.query(func.count(Dossier.id)).filter(
                and_(
                    extract('month', Dossier.completed_at) == month,
                    extract('year', Dossier.completed_at) == year,
                    Dossier.statut == StatusDossier.COMPLETE
                )
            ).scalar() or 0
            
            # Dossiers en retard à la fin du mois
            last_day_of_month = date(year, month, 1) + timedelta(days=32)
            last_day_of_month = last_day_of_month.replace(day=1) - timedelta(days=1)
            
            overdue = db.query(func.count(Dossier.id)).filter(
                and_(
                    Dossier.date_echeance < last_day_of_month,
                    Dossier.statut != StatusDossier.COMPLETE,
                    Dossier.statut != StatusDossier.ARCHIVE,
                    Dossier.created_at <= last_day_of_month
                )
            ).scalar() or 0
            
            data.append({
                "date": month_date.strftime("%b %Y"),
                "created": created,
                "completed": completed,
                "overdue": overdue
            })
    
    # Si aucune donnée, retourner au moins le jour actuel avec les compteurs actuels
    if not data or all(d['created'] == 0 and d['completed'] == 0 and d['overdue'] == 0 for d in data):
        # Importer le modèle DeclarationFiscale
        from app.models.declaration_fiscale import DeclarationFiscale
        
        # Compter toutes les tâches (échéances + déclarations)
        total_echeances = db.query(func.count(Echeance.id)).scalar() or 0
        total_declarations = db.query(func.count(DeclarationFiscale.id)).scalar() or 0
        total_taches = total_echeances + total_declarations
        
        # Compter les complétées
        echeances_completes = db.query(func.count(Echeance.id)).filter(
            Echeance.statut == 'COMPLETE'
        ).scalar() or 0
        declarations_completes = db.query(func.count(DeclarationFiscale.id)).filter(
            DeclarationFiscale.statut.in_(['TELEDECLAREE', 'VALIDEE'])
        ).scalar() or 0
        total_completes = echeances_completes + declarations_completes
        
        # Compter les en retard
        echeances_en_retard = db.query(func.count(Echeance.id)).filter(
            and_(
                Echeance.date_echeance < today,
                Echeance.statut != 'COMPLETE'
            )
        ).scalar() or 0
        declarations_en_retard = db.query(func.count(DeclarationFiscale.id)).filter(
            and_(
                DeclarationFiscale.date_limite < today,
                ~DeclarationFiscale.statut.in_(['TELEDECLAREE', 'VALIDEE'])
            )
        ).scalar() or 0
        total_retard = echeances_en_retard + declarations_en_retard
        
        logger.info(f"Pas de données historiques, retour des compteurs actuels: total={total_taches}, completes={total_completes}, retard={total_retard}")
        
        # Retourner au moins un point avec les données actuelles
        return [{
            "date": today.strftime("%d/%m"),
            "created": total_taches,
            "completed": total_completes,
            "overdue": total_retard
        }]
    
    logger.info(f"Retour de {len(data)} points de données")
    return data


@router.get("/services-distribution")
async def get_services_distribution(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    period: str = None
):
    """Récupérer la distribution des dossiers par type de service"""
    # Déterminer la date de début selon la période
    today = date.today()
    if period == 'today':
        start_date = today
    elif period == 'week':
        start_date = today - timedelta(days=7)
    elif period == 'month':
        start_date = today - timedelta(days=30)
    elif period == 'quarter':
        start_date = today - timedelta(days=90)
    elif period == 'year':
        start_date = today - timedelta(days=365)
    else:
        start_date = None
        
    # Compter les dossiers par type principal
    query = db.query(
        Dossier.type_dossier,
        func.count(Dossier.id).label('count')
    ).filter(
        Dossier.statut != StatusDossier.ARCHIVE
    )
    if start_date:
        query = query.filter(Dossier.created_at >= start_date)
    distribution = query.group_by(Dossier.type_dossier).all()
    
    # Formatter les données pour le graphique
    data = []
    color_map = {
        'COMPTABILITE': '#72C2F1',
        'TVA': '#F59E0B',
        'PAIE': '#10B981',
        'JURIDIQUE': '#8B5CF6',
        'LIASSE_FISCALE': '#EF4444',
        'CREATION_ENTREPRISE': '#3B82F6',
        'AUTRE': '#6B7280'
    }
    
    for type_dossier, count in distribution:
        data.append({
            "name": type_dossier.replace('_', ' ').title(),
            "value": count,
            "color": color_map.get(type_dossier, '#6B7280')
        })
    
    return data