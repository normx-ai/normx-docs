from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case, extract
from datetime import datetime, date, timedelta
from typing import List, Optional

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.dossier import Dossier
from app.models.echeance import Echeance
from app.models.declaration_fiscale import DeclarationFiscale

router = APIRouter()


@router.get("/avancement")
async def get_avancement_global(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    periode: str = Query("current_year", description="Période: current_year, current_quarter, current_month, all"),
    statut: str = Query("all", description="Statut: all, completed, in_progress, overdue")
):
    """Récupérer l'avancement global par client"""
    
    # Déterminer la période de filtrage
    today = date.today()
    start_date = None
    end_date = None
    
    if periode == "current_month":
        start_date = date(today.year, today.month, 1)
        # Dernier jour du mois
        if today.month == 12:
            end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)
    elif periode == "current_quarter":
        current_quarter = (today.month - 1) // 3
        start_date = date(today.year, current_quarter * 3 + 1, 1)
        # Fin du trimestre
        end_quarter_month = (current_quarter + 1) * 3
        if end_quarter_month > 12:
            end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(today.year, end_quarter_month + 1, 1) - timedelta(days=1)
    elif periode == "current_year":
        start_date = date(today.year, 1, 1)
        end_date = date(today.year, 12, 31)
    
    # Récupérer tous les dossiers avec leurs échéances
    dossiers = db.query(Dossier).all()
    
    results = []
    
    for dossier in dossiers:
        # Statistiques des échéances
        echeances_query = db.query(Echeance).filter(
            Echeance.dossier_id == dossier.id
        )
        
        # Appliquer le filtre de période si nécessaire
        if start_date and end_date:
            echeances_query = echeances_query.filter(
                and_(
                    Echeance.date_echeance >= start_date,
                    Echeance.date_echeance <= end_date
                )
            )
        
        # Compter les échéances
        total_echeances = echeances_query.count()
        echeances_completes = echeances_query.filter(
            Echeance.statut == 'COMPLETE'
        ).count()
        echeances_en_retard = echeances_query.filter(
            and_(
                Echeance.date_echeance < today,
                Echeance.statut != 'COMPLETE'
            )
        ).count()
        
        # Si c'est un dossier fiscal, compter aussi les déclarations
        total_declarations = 0
        declarations_completes = 0
        declarations_en_retard = 0
        
        if dossier.type_dossier in ['FISCALITE', 'TVA']:
            declarations_query = db.query(DeclarationFiscale).filter(
                DeclarationFiscale.dossier_id == dossier.id
            )
            
            if start_date and end_date:
                declarations_query = declarations_query.filter(
                    and_(
                        DeclarationFiscale.date_limite >= start_date,
                        DeclarationFiscale.date_limite <= end_date
                    )
                )
            
            total_declarations = declarations_query.count()
            declarations_completes = declarations_query.filter(
                DeclarationFiscale.statut.in_(['TELEDECLAREE', 'VALIDEE'])
            ).count()
            declarations_en_retard = declarations_query.filter(
                and_(
                    DeclarationFiscale.date_limite < today,
                    ~DeclarationFiscale.statut.in_(['TELEDECLAREE', 'VALIDEE'])
                )
            ).count()
        
        # Totaux
        total_taches = total_echeances + total_declarations
        taches_completes = echeances_completes + declarations_completes
        taches_en_retard = echeances_en_retard + declarations_en_retard
        
        # Appliquer le filtre de statut
        if statut == "completed" and taches_completes == 0:
            continue
        elif statut == "in_progress" and (taches_completes == total_taches or total_taches == 0):
            continue
        elif statut == "overdue" and taches_en_retard == 0:
            continue
        
        # Calculer le pourcentage
        pourcentage = 0
        if total_taches > 0:
            pourcentage = round((taches_completes / total_taches) * 100)
        
        # Détails par mois pour les échéances
        details_par_mois = []
        
        # Récupérer les mois uniques
        mois_data = db.query(
            extract('month', Echeance.date_echeance).label('mois'),
            extract('year', Echeance.date_echeance).label('annee'),
            func.count(Echeance.id).label('total'),
            func.sum(case([(Echeance.statut == 'COMPLETE', 1)], else_=0)).label('completes'),
            func.sum(case([
                (and_(Echeance.date_echeance < today, Echeance.statut != 'COMPLETE'), 1)
            ], else_=0)).label('en_retard')
        ).filter(
            Echeance.dossier_id == dossier.id
        ).group_by(
            extract('year', Echeance.date_echeance),
            extract('month', Echeance.date_echeance)
        ).order_by(
            extract('year', Echeance.date_echeance),
            extract('month', Echeance.date_echeance)
        ).all()
        
        mois_noms = {
            1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril',
            5: 'Mai', 6: 'Juin', 7: 'Juillet', 8: 'Août',
            9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
        }
        
        for mois, annee, total, completes, en_retard in mois_data:
            details_par_mois.append({
                'mois': mois_noms[int(mois)],
                'annee': int(annee),
                'total': total or 0,
                'completes': completes or 0,
                'en_retard': en_retard or 0
            })
        
        results.append({
            'client_id': dossier.id,  # Utiliser dossier.id car pas de client_id
            'nom_client': dossier.nom_client,
            'total_echeances': total_taches,
            'echeances_completes': taches_completes,
            'echeances_en_retard': taches_en_retard,
            'pourcentage_complete': pourcentage,
            'details_par_mois': details_par_mois
        })
    
    # Grouper par nom_client (car plusieurs dossiers peuvent avoir le même client)
    grouped_results = {}
    for result in results:
        nom = result['nom_client']
        if nom not in grouped_results:
            grouped_results[nom] = {
                'client_id': result['client_id'],
                'nom_client': nom,
                'total_echeances': 0,
                'echeances_completes': 0,
                'echeances_en_retard': 0,
                'details_par_mois': []
            }
        
        grouped_results[nom]['total_echeances'] += result['total_echeances']
        grouped_results[nom]['echeances_completes'] += result['echeances_completes']
        grouped_results[nom]['echeances_en_retard'] += result['echeances_en_retard']
        
        # Fusionner les détails par mois
        for detail in result['details_par_mois']:
            # Chercher si ce mois existe déjà
            found = False
            for existing in grouped_results[nom]['details_par_mois']:
                if existing['mois'] == detail['mois'] and existing['annee'] == detail['annee']:
                    existing['total'] += detail['total']
                    existing['completes'] += detail['completes']
                    existing['en_retard'] += detail['en_retard']
                    found = True
                    break
            if not found:
                grouped_results[nom]['details_par_mois'].append(detail)
    
    # Recalculer les pourcentages
    final_results = []
    for nom, data in grouped_results.items():
        if data['total_echeances'] > 0:
            data['pourcentage_complete'] = round((data['echeances_completes'] / data['total_echeances']) * 100)
        else:
            data['pourcentage_complete'] = 0
        
        # Trier les détails par mois
        data['details_par_mois'].sort(key=lambda x: (x['annee'], 
            ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 
             'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'].index(x['mois'])))
        
        final_results.append(data)
    
    # Trier par nom de client
    final_results.sort(key=lambda x: x['nom_client'])
    
    return final_results


@router.get("/historique/{echeance_id}")
async def get_historique_echeance(
    echeance_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupérer l'historique d'une échéance"""
    # À implémenter avec le modèle HistoriqueEcheance
    return {
        "echeance_id": echeance_id,
        "historique": []
    }