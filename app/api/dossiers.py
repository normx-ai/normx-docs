from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query, Form
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import date, datetime, timedelta
import logging

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_cabinet_id
from app.models.user import User
from app.models.dossier import Dossier as DossierModel, StatusDossier, TypeDossier
from app.models.alerte import Alerte
from app.models.historique import HistoriqueDossier
from app.schemas.dossier import (
    DossierCreate, Dossier, DossierUpdate, DossierStatusUpdate,
    DossierWithDetails, DailyPoint
)
from app.services.alerte_service import AlerteService

router = APIRouter()
logger = logging.getLogger(__name__)


def generate_dossier_reference(db: Session, type_dossier: str, cabinet_id: int) -> str:
    """Génère une référence automatique pour un dossier"""
    current_year = datetime.now().year
    
    # Préfixes par type de dossier
    type_prefixes = {
        'COMPTABILITE': 'COMPTA',
        'FISCALITE': 'FISCAL',
        'PAIE': 'PAIE',
        'JURIDIQUE': 'JURID',
        'AUDIT': 'AUDIT',
        'CONSEIL': 'CONSEIL',
        'AUTRE': 'AUTRE'
    }
    
    prefix = type_prefixes.get(type_dossier, 'DOSS')
    
    # Compter les dossiers de ce type pour cette année et ce cabinet
    count = db.query(DossierModel).filter(
        and_(
            DossierModel.cabinet_id == cabinet_id,
            DossierModel.type_dossier == type_dossier,
            DossierModel.reference.like(f"{prefix}-{current_year}-%")
        )
    ).count()
    
    next_number = count + 1
    return f"{prefix}-{current_year}-{str(next_number).zfill(4)}"


def calculate_service_echeance(service_type: str, periode_comptable: str) -> str:
    """Calcule la date d'échéance spécifique pour un service donné"""
    if not periode_comptable:
        return ''
    
    try:
        # Format attendu: "Janvier 2025", "Février 2025", etc.
        mois = {
            'janvier': 0, 'février': 1, 'mars': 2, 'avril': 3,
            'mai': 4, 'juin': 5, 'juillet': 6, 'août': 7,
            'septembre': 8, 'octobre': 9, 'novembre': 10, 'décembre': 11
        }
        
        parts = periode_comptable.lower().split(' ')
        if len(parts) != 2:
            return ''
        
        mois_nom = parts[0]
        annee = int(parts[1])
        
        if mois_nom not in mois or not annee:
            return ''
        
        mois_index = mois[mois_nom]
        
        # Dates spécifiques par service
        service_jours = {
            'COMPTABILITE': 10,
            'FISCALITE': 15,
            'PAIE': 5,
            'JURIDIQUE': 20,
            'AUDIT': 30,
            'CONSEIL': 15,
            'AUTRE': 15
        }
        
        jour_echeance = service_jours.get(service_type, 15)
        mois_echeance = mois_index + 1
        annee_echeance = annee
        
        # Gérer le passage à l'année suivante
        if mois_echeance > 11:
            mois_echeance = 0
            annee_echeance += 1
        
        from datetime import date
        date_echeance = date(annee_echeance, mois_echeance + 1, jour_echeance)
        
        # Si la date tombe un weekend, reporter au lundi suivant
        if date_echeance.weekday() == 6:  # Dimanche
            date_echeance = date_echeance.replace(day=date_echeance.day + 1)
        elif date_echeance.weekday() == 5:  # Samedi
            date_echeance = date_echeance.replace(day=date_echeance.day + 2)
        
        return date_echeance.isoformat()
    except:
        return ''


@router.post("/", response_model=dict)
async def create_dossier(
    dossier_data: DossierCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crée un ou plusieurs dossiers selon les services sélectionnés"""
    created_dossiers = []
    
    # Services à traiter : service principal + services multiples
    services_to_create = [dossier_data.type_dossier.value]
    
    # Ajouter les services multiples (s'ils sont différents du service principal)
    for service in dossier_data.services_list:
        if service != dossier_data.type_dossier.value and service not in services_to_create:
            services_to_create.append(service)
    
    # Trouver le responsable du client automatiquement
    from app.models.client import Client
    client = db.query(Client).filter(Client.nom == dossier_data.nom_client).first()
    responsable_id_auto = None
    if client and client.user_id:
        responsable_id_auto = client.user_id
    
    # Créer un dossier pour chaque service
    for service_type in services_to_create:
        # Calculer la date d'échéance spécifique pour ce service
        date_echeance_str = calculate_service_echeance(service_type, dossier_data.periode_comptable)
        date_echeance_obj = None
        if date_echeance_str:
            from datetime import datetime as dt2
            date_echeance_obj = dt2.fromisoformat(date_echeance_str).date()
        
        # Générer une référence spécifique pour ce service
        reference = generate_dossier_reference(db, service_type)
        
        # Préparer les données du dossier
        dossier_dict = dossier_data.dict()
        dossier_dict.pop('priorite', None)  # Calculé automatiquement
        dossier_dict['reference'] = reference
        dossier_dict['type_dossier'] = service_type
        dossier_dict['date_echeance'] = date_echeance_obj
        dossier_dict['services_list'] = [service_type]  # Un seul service par dossier
        dossier_dict['responsable_id'] = responsable_id_auto  # Assignation automatique
        
        # Créer le dossier
        dossier = DossierModel(
            **dossier_dict,
            user_id=current_user.id,
            statut=StatusDossier.NOUVEAU
        )
        
        # Calculer la priorité automatiquement
        if dossier.date_echeance:
            dossier.priorite = dossier.priorite_automatique
        
        db.add(dossier)
        db.flush()  # Pour obtenir l'ID
        
        # Ajouter à l'historique
        historique = HistoriqueDossier(
            dossier_id=dossier.id,
            user_id=current_user.id,
            action="creation",
            new_value=dossier.statut.value,
            commentaire=f"Dossier {service_type} créé automatiquement"
        )
        db.add(historique)
        
        # Traitement spécial pour les dossiers FISCALITE
        if service_type == 'FISCALITE':
            logger.info(f"Création de dossier FISCALITE pour {dossier_data.nom_client}")
            from app.services.fiscal_service import create_declarations_fiscales, create_echeances_from_declarations
            from datetime import datetime as dt
            
            # Déterminer l'année fiscale
            annee_fiscale = dt.now().year
            if dossier_data.exercice_fiscal:
                try:
                    annee_fiscale = int(dossier_data.exercice_fiscal)
                except:
                    pass
            
            # Utiliser le service fiscal pour créer toutes les déclarations selon le statut juridique
            type_entreprise = dossier_data.type_entreprise or 'SARL'  # Valeur par défaut
            
            # Créer toutes les déclarations fiscales selon le statut juridique
            count_declarations = create_declarations_fiscales(
                db=db,
                dossier_id=dossier.id,
                type_entreprise=type_entreprise,
                annee_fiscale=annee_fiscale
            )
            logger.info(f"{count_declarations} déclarations fiscales créées pour {type_entreprise}")
            
            # Créer les échéances basées sur les déclarations
            count_echeances = create_echeances_from_declarations(
                db=db,
                dossier_id=dossier.id,
                type_entreprise=type_entreprise,
                annee_fiscale=annee_fiscale
            )
            logger.info(f"{count_echeances} échéances fiscales créées")
        
        # Créer les échéances pour les 12 mois (si c'est un dossier comptabilité ou paie)
        elif service_type in ['COMPTABILITE', 'PAIE']:
            from app.models.echeance import Echeance
            from app.models.saisie import SaisieComptable
            
            # Déterminer l'année de départ
            from datetime import datetime as dt
            annee_depart = dt.now().year
            if dossier_data.exercice_fiscal:
                try:
                    annee_depart = int(dossier_data.exercice_fiscal)
                except:
                    pass
            
            # Mois en français
            mois_noms = [
                'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
            ]
            
            # Types de journaux selon le service
            if service_type == 'COMPTABILITE':
                types_journaux = ['BANQUE', 'CAISSE', 'OD', 'ACHATS', 'VENTES', 'PAIE']
            elif service_type == 'PAIE':
                types_journaux = ['DSN', 'BULLETINS', 'DUCS', 'DECLARATION_SOCIALE', 'CHARGES_SOCIALES']
            else:
                types_journaux = ['GENERAL']
            
            # Créer une échéance pour chaque mois
            for mois_idx in range(12):
                mois_num = mois_idx + 1
                periode_label = f"{mois_noms[mois_idx]} {annee_depart}"
                
                # Calculer la date d'échéance pour ce mois
                date_echeance_str = calculate_service_echeance(service_type, periode_label)
                if date_echeance_str:
                    date_echeance_obj = dt.fromisoformat(date_echeance_str).date()
                    
                    echeance = Echeance(
                        dossier_id=dossier.id,
                        mois=mois_num,
                        annee=annee_depart,
                        periode_label=periode_label,
                        date_echeance=date_echeance_obj,
                        statut='A_FAIRE'
                    )
                    db.add(echeance)
                    db.flush()  # Pour obtenir l'ID de l'échéance
                    
                    # Créer les saisies comptables pour chaque type de journal
                    for type_journal in types_journaux:
                        saisie = SaisieComptable(
                            dossier_id=dossier.id,
                            echeance_id=echeance.id,
                            type_journal=type_journal,
                            mois=mois_num,
                            annee=annee_depart,
                            est_complete=False
                        )
                        db.add(saisie)
                    
                    # Créer les documents requis pour cette échéance
                    from app.models.document_requis import DocumentRequis
                    from app.models.document import TypeDocument
                    
                    # Types de documents requis par service
                    documents_par_service = {
                        'COMPTABILITE': [TypeDocument.RELEVE_BANCAIRE, TypeDocument.FACTURE_ACHAT, TypeDocument.FACTURE_VENTE],
                        'FISCALITE': [TypeDocument.DECLARATION_TVA, TypeDocument.DECLARATION_IMPOT],
                        'PAIE': [TypeDocument.ETAT_PAIE, TypeDocument.DECLARATION_SOCIALE],
                        'JURIDIQUE': [TypeDocument.CONTRAT, TypeDocument.COURRIER],
                        'AUDIT': [TypeDocument.RELEVE_BANCAIRE, TypeDocument.FACTURE_ACHAT, TypeDocument.FACTURE_VENTE],
                        'CONSEIL': [TypeDocument.CONTRAT, TypeDocument.COURRIER],
                        'AUTRE': [TypeDocument.AUTRE]
                    }
                    
                    docs_requis = documents_par_service.get(service_type, [TypeDocument.AUTRE])
                    for type_doc in docs_requis:
                        doc_requis = DocumentRequis(
                            dossier_id=dossier.id,
                            echeance_id=echeance.id,
                            type_document=type_doc,
                            mois=mois_num,
                            annee=annee_depart,
                            est_applicable=True,
                            est_fourni=False
                        )
                        db.add(doc_requis)
        
        created_dossiers.append(dossier)
    
    db.commit()
    
    # Rafraîchir tous les dossiers créés
    for dossier in created_dossiers:
        db.refresh(dossier)
    
    # Retourner un résumé au lieu de la liste complète pour éviter les erreurs de sérialisation
    return {
        "created_count": len(created_dossiers),
        "dossiers": [
            {
                "id": d.id,
                "reference": d.reference,
                "type_dossier": d.type_dossier.value,
                "nom_client": d.nom_client,
                "date_echeance": d.date_echeance.isoformat() if d.date_echeance else None,
                "statut": d.statut.value,
                "priorite": d.priorite.value
            }
            for d in created_dossiers
        ]
    }


@router.get("", response_model=List[DossierWithDetails])
@router.get("/", response_model=List[DossierWithDetails])
async def list_dossiers(
    status: Optional[StatusDossier] = Query(None, description="Filtrer par statut"),
    responsable_id: Optional[int] = Query(None, description="Filtrer par responsable"),
    urgent: Optional[bool] = Query(None, description="Dossiers urgents uniquement"),
    limit: int = Query(100, ge=1, le=500, description="Nombre maximum de résultats"),
    offset: int = Query(0, ge=0, description="Décalage pour la pagination"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from sqlalchemy.orm import joinedload, selectinload
    
    # Utiliser joinedload pour éviter les requêtes N+1
    query = db.query(DossierModel).filter(
        DossierModel.cabinet_id == current_user.cabinet_id
    ).options(
        selectinload(DossierModel.echeances),
        selectinload(DossierModel.alertes),
        selectinload(DossierModel.documents),
        joinedload(DossierModel.responsable)
    )
    
    # RESTRICTION D'ACCÈS SELON LE RÔLE
    if current_user.role == "collaborateur":
        # Les collaborateurs voient les dossiers des clients qui leur sont assignés
        from app.models.client import Client
        # Récupérer les noms des clients assignés à cet utilisateur
        clients_assignes = db.query(Client).filter(Client.user_id == current_user.id).all()
        noms_clients = [client.nom for client in clients_assignes]
        
        if noms_clients:
            query = query.filter(DossierModel.nom_client.in_(noms_clients))
        else:
            # Si aucun client assigné, ne montrer aucun dossier
            query = query.filter(False)  # Condition impossible
    elif current_user.role == "manager":
        # Les managers voient tous les dossiers
        pass  # Voir tous les dossiers
    elif current_user.role == "admin":
        # Les admins voient tous les dossiers
        pass  # Voir tous les dossiers
    
    # Appliquer les filtres supplémentaires
    if status:
        query = query.filter(DossierModel.statut == status)
    if responsable_id:
        query = query.filter(DossierModel.responsable_id == responsable_id)
    if urgent:
        today = date.today()
        query = query.filter(
            or_(
                DossierModel.date_echeance < today,  # En retard
                DossierModel.date_echeance <= today + timedelta(days=3)  # Proche
            )
        )
    
    # Ajouter la pagination
    total = query.count()
    dossiers = query.offset(offset).limit(limit).all()
    
    # Ajouter les infos de pagination dans les headers de réponse
    # (sera fait dans la réponse)
    
    # Mettre à jour automatiquement les priorités et statuts, puis enrichir avec les détails
    result = []
    for dossier in dossiers:
        statut_change = False
        
        # Mettre à jour la priorité automatiquement si le dossier a une date d'échéance
        if dossier.date_echeance and dossier.statut != StatusDossier.COMPLETE:
            nouvelle_priorite = dossier.priorite_automatique
            if dossier.priorite != nouvelle_priorite:
                dossier.priorite = nouvelle_priorite
                statut_change = True
        
        # Auto-transition: EN_COURS -> EN_ATTENTE si pas d'activité depuis 7 jours
        if dossier.peut_passer_en_attente():
            old_status = dossier.statut
            dossier.statut = StatusDossier.EN_ATTENTE
            dossier.updated_at = datetime.utcnow()
            
            # Ajouter à l'historique
            historique = HistoriqueDossier(
                dossier_id=dossier.id,
                user_id=current_user.id,
                action="auto_status_change",
                old_value=old_status.value,
                new_value=StatusDossier.EN_ATTENTE.value,
                commentaire="Passage automatique en attente (pas d'activité depuis 7 jours)"
            )
            db.add(historique)
            statut_change = True
        
        if statut_change:
            db.commit()
        
        dossier_dict = dossier.__dict__.copy()
        dossier_dict['responsable_name'] = dossier.responsable.full_name if dossier.responsable else None
        dossier_dict['alerts_count'] = len([a for a in dossier.alertes if a.active])
        # Retirer temporairement le compte des documents car la table a une structure différente
        dossier_dict['documents_count'] = 0
        
        # Ajouter les informations sur les échéances
        if hasattr(dossier, 'echeances') and dossier.echeances:
            dossier_dict['echeances'] = dossier.echeances
            dossier_dict['echeances_totales'] = len(dossier.echeances)
            dossier_dict['echeances_completees'] = len([e for e in dossier.echeances if e.statut == 'COMPLETE'])
            prochaine = dossier.prochaine_echeance
            dossier_dict['prochaine_echeance_date'] = prochaine.date_echeance if prochaine else None
        else:
            dossier_dict['echeances'] = []
            dossier_dict['echeances_totales'] = 0
            dossier_dict['echeances_completees'] = 0
            dossier_dict['prochaine_echeance_date'] = dossier.date_echeance
        
        result.append(DossierWithDetails(**dossier_dict))
    
    return result


@router.get("/daily-point", response_model=DailyPoint)
async def get_daily_point(
    date_point: Optional[date] = Query(None, description="Date du point (par défaut aujourd'hui)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_date = date_point or date.today()
    
    # Dossiers en retard
    dossiers_retard = db.query(DossierModel).filter(
        and_(
            DossierModel.date_echeance < target_date,
            DossierModel.statut != StatusDossier.COMPLETE
        )
    ).all()
    
    # Dossiers à traiter aujourd'hui
    dossiers_aujourdhui = db.query(DossierModel).filter(
        and_(
            DossierModel.date_echeance == target_date,
            DossierModel.statut != StatusDossier.COMPLETE
        )
    ).all()
    
    # Dossiers urgents (3 jours)
    dossiers_urgents = db.query(DossierModel).filter(
        and_(
            DossierModel.date_echeance <= target_date + timedelta(days=3),
            DossierModel.date_echeance > target_date,
            DossierModel.statut != StatusDossier.COMPLETE
        )
    ).all()
    
    # Dossiers complétés aujourd'hui
    dossiers_completes = db.query(DossierModel).filter(
        and_(
            DossierModel.completed_at >= target_date,
            DossierModel.completed_at < target_date + timedelta(days=1)
        )
    ).all()
    
    # Statistiques
    total_actifs = db.query(DossierModel).filter(
        DossierModel.statut.in_([StatusDossier.NOUVEAU, StatusDossier.EN_COURS, StatusDossier.EN_ATTENTE])
    ).count()
    
    def enrich_dossiers(dossiers):
        result = []
        for d in dossiers:
            d_dict = d.__dict__.copy()
            d_dict['responsable_name'] = d.responsable.full_name if d.responsable else None
            d_dict['alerts_count'] = len([a for a in d.alertes if a.active])
            # Retirer temporairement le compte des documents car la table a une structure différente
            d_dict['documents_count'] = 0
            
            # Ajouter les informations sur les échéances
            if hasattr(d, 'echeances') and d.echeances:
                d_dict['echeances'] = d.echeances
                d_dict['echeances_totales'] = len(d.echeances)
                d_dict['echeances_completees'] = len([e for e in d.echeances if e.statut == 'COMPLETE'])
                prochaine = d.prochaine_echeance
                d_dict['prochaine_echeance_date'] = prochaine.date_echeance if prochaine else None
            else:
                d_dict['echeances'] = []
                d_dict['echeances_totales'] = 0
                d_dict['echeances_completees'] = 0
                d_dict['prochaine_echeance_date'] = d.date_echeance
            
            result.append(DossierWithDetails(**d_dict))
        return result
    
    return DailyPoint(
        date=target_date,
        dossiers_urgents=enrich_dossiers(dossiers_urgents),
        dossiers_retard=enrich_dossiers(dossiers_retard),
        dossiers_a_traiter=enrich_dossiers(dossiers_aujourdhui),
        dossiers_completes=enrich_dossiers(dossiers_completes),
        statistiques={
            "total_actifs": total_actifs,
            "en_retard": len(dossiers_retard),
            "aujourdhui": len(dossiers_aujourdhui),
            "urgents": len(dossiers_urgents),
            "completes": len(dossiers_completes)
        }
    )


@router.get("/stats/echeances")
async def get_echeances_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtenir les statistiques des échéances"""
    from app.models.echeance import Echeance
    from app.models.client import Client
    
    # Obtenir les dossiers accessibles selon le rôle
    query = db.query(DossierModel)
    
    if current_user.role == "collaborateur":
        clients_assignes = db.query(Client).filter(Client.user_id == current_user.id).all()
        noms_clients = [client.nom for client in clients_assignes]
        if noms_clients:
            query = query.filter(DossierModel.nom_client.in_(noms_clients))
        else:
            return {"en_retard": 0, "urgentes": 0, "a_faire": 0, "completes": 0, "total": 0}
    
    # Obtenir les IDs des dossiers accessibles
    dossiers = query.all()
    dossier_ids = [d.id for d in dossiers]
    
    logger.info(f"Stats échéances - Dossiers trouvés: {len(dossiers)}")
    for d in dossiers:
        logger.info(f"  - Dossier {d.id}: {d.reference} ({d.type_dossier}) - {d.nom_client}")
    
    if not dossier_ids:
        return {"en_retard": 0, "urgentes": 0, "a_faire": 0, "completes": 0, "total": 0}
    
    # Requête sur les échéances
    today = date.today()
    echeances_query = db.query(Echeance).filter(Echeance.dossier_id.in_(dossier_ids))
    
    # Debug : lister toutes les échéances
    all_echeances = echeances_query.all()
    logger.info(f"Stats échéances - Total échéances trouvées: {len(all_echeances)}")
    for e in all_echeances:
        logger.info(f"  - Échéance {e.id}: dossier {e.dossier_id}, statut '{e.statut}', période {e.periode_label}")
    
    # Compter les échéances classiques (COMPTABILITE)
    total_echeances = len(all_echeances)
    completes_echeances = echeances_query.filter(Echeance.statut == 'COMPLETE').count()
    
    # Ajouter les déclarations fiscales complètes (FISCALITE)
    from app.models.declaration_fiscale import DeclarationFiscale
    declarations_fiscales = db.query(DeclarationFiscale).filter(DeclarationFiscale.dossier_id.in_(dossier_ids)).all()
    completes_fiscales = sum(1 for d in declarations_fiscales if d.statut in ['TELEDECLAREE', 'VALIDEE'])
    
    # Note: Les dossiers PAIE utilisent aussi des échéances mensuelles (comme COMPTABILITE)
    # avec des saisies pour DSN, bulletins, etc. Donc ils sont déjà comptés dans total_echeances
    
    logger.info(f"Stats échéances - Échéances (COMPTA + PAIE): {completes_echeances}/{total_echeances}")
    logger.info(f"Stats échéances - Déclarations fiscales: {completes_fiscales}/{len(declarations_fiscales)}")
    
    # Total global (échéances + déclarations fiscales)
    total = total_echeances + len(declarations_fiscales)
    completes = completes_echeances + completes_fiscales
    logger.info(f"Stats échéances - TOTAL GLOBAL: {completes}/{total}")
    # Compter les retards (échéances COMPTA/PAIE + déclarations FISCALITE)
    en_retard_echeances = echeances_query.filter(
        and_(
            Echeance.date_echeance < today,
            Echeance.statut != 'COMPLETE'
        )
    ).count()
    
    en_retard_fiscales = sum(1 for d in declarations_fiscales 
                            if d.date_limite < today and d.statut not in ['TELEDECLAREE', 'VALIDEE'])
    
    en_retard = en_retard_echeances + en_retard_fiscales
    
    # Échéances critiques (en retard + dans les 3 prochains jours)
    date_limite_critique = today + timedelta(days=3)
    critiques_echeances = echeances_query.filter(
        and_(
            Echeance.date_echeance <= date_limite_critique,
            Echeance.statut != 'COMPLETE'
        )
    ).count()
    
    critiques_fiscales = sum(1 for d in declarations_fiscales 
                            if d.date_limite <= date_limite_critique and d.statut not in ['TELEDECLAREE', 'VALIDEE'])
    
    critiques = critiques_echeances + critiques_fiscales
    
    # Échéances urgentes (dans les 7 prochains jours, non en retard)
    date_limite_urgente = today + timedelta(days=7)
    urgentes_echeances = echeances_query.filter(
        and_(
            Echeance.date_echeance >= today,
            Echeance.date_echeance <= date_limite_urgente,
            Echeance.statut != 'COMPLETE'
        )
    ).count()
    
    urgentes_fiscales = sum(1 for d in declarations_fiscales 
                           if today <= d.date_limite <= date_limite_urgente and d.statut not in ['TELEDECLAREE', 'VALIDEE'])
    
    urgentes = urgentes_echeances + urgentes_fiscales
    
    # À faire = non complètes et non en retard
    a_faire_echeances = echeances_query.filter(
        and_(
            Echeance.date_echeance >= today,
            Echeance.statut != 'COMPLETE'
        )
    ).count()
    
    a_faire_fiscales = sum(1 for d in declarations_fiscales 
                          if d.date_limite >= today and d.statut not in ['TELEDECLAREE', 'VALIDEE'])
    
    a_faire = a_faire_echeances + a_faire_fiscales
    
    return {
        "en_retard": en_retard,
        "critiques": critiques,
        "urgentes": urgentes,
        "a_faire": a_faire,
        "completes": completes,
        "total": total
    }


@router.get("/{dossier_id}", response_model=Dossier)
async def get_dossier(
    dossier_id: int,
    current_user: User = Depends(get_current_user),
    cabinet_id: int = Depends(get_current_cabinet_id),
    db: Session = Depends(get_db)
):
    dossier = db.query(DossierModel).filter(
        DossierModel.id == dossier_id,
        DossierModel.cabinet_id == cabinet_id
    ).first()
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")
    
    # VÉRIFICATION DES PERMISSIONS
    if current_user.role == "collaborateur":
        # Les collaborateurs ne peuvent voir que les dossiers des clients qui leur sont assignés
        from app.models.client import Client
        clients_assignes = db.query(Client).filter(Client.user_id == current_user.id).all()
        noms_clients = [client.nom for client in clients_assignes]
        
        if dossier.nom_client not in noms_clients:
            raise HTTPException(status_code=403, detail="Accès refusé : ce client ne vous est pas assigné")
    
    # Auto-transition: NOUVEAU -> EN_COURS quand on consulte le dossier
    if dossier.peut_passer_en_cours():
        old_status = dossier.statut
        dossier.statut = StatusDossier.EN_COURS
        dossier.updated_at = datetime.utcnow()
        
        # Ajouter à l'historique
        historique = HistoriqueDossier(
            dossier_id=dossier_id,
            user_id=current_user.id,
            action="auto_status_change",
            old_value=old_status.value,
            new_value=StatusDossier.EN_COURS.value,
            commentaire="Passage automatique en cours lors de la consultation"
        )
        db.add(historique)
        db.commit()
        db.refresh(dossier)
    
    return dossier


@router.put("/{dossier_id}", response_model=Dossier)
async def update_dossier(
    dossier_id: int,
    dossier_update: DossierUpdate,
    current_user: User = Depends(get_current_user),
    cabinet_id: int = Depends(get_current_cabinet_id),
    db: Session = Depends(get_db)
):
    """Mettre à jour un dossier"""
    dossier = db.query(DossierModel).filter(
        DossierModel.id == dossier_id,
        DossierModel.cabinet_id == cabinet_id
    ).first()
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")
    
    # VÉRIFICATION DES PERMISSIONS
    if current_user.role == "collaborateur":
        from app.models.client import Client
        clients_assignes = db.query(Client).filter(Client.user_id == current_user.id).all()
        noms_clients = [client.nom for client in clients_assignes]
        
        if dossier.nom_client not in noms_clients:
            raise HTTPException(status_code=403, detail="Accès refusé : ce client ne vous est pas assigné")
    
    # Mettre à jour les champs fournis
    update_data = dossier_update.dict(exclude_unset=True)
    
    # Vérifier si services_list a changé pour créer des dossiers manquants
    old_services = set(dossier.services_list or [])
    new_services = set(update_data.get('services_list', dossier.services_list or []))
    services_added = new_services - old_services
    
    for field, value in update_data.items():
        setattr(dossier, field, value)
    
    dossier.updated_at = datetime.utcnow()
    
    # Créer des dossiers pour les nouveaux services ajoutés
    created_dossiers = []
    if services_added:
        logger.info(f"Nouveaux services détectés pour {dossier.nom_client}: {services_added}")
        
        # Préparer les données de base du dossier
        base_data = {
            'nom_client': dossier.nom_client,
            'type_entreprise': dossier.type_entreprise,
            'numero_siret': dossier.numero_siret,
            'periode_comptable': dossier.periode_comptable,
            'exercice_fiscal': dossier.exercice_fiscal,
            'contact_client': dossier.contact_client,
            'telephone_client': dossier.telephone_client,
            'description': dossier.description,
            'notes': dossier.notes,
            'responsable_id': dossier.responsable_id
        }
        
        for service_type in services_added:
            if service_type == dossier.type_dossier.value:
                continue  # Ne pas recréer le dossier actuel
                
            # Calculer la date d'échéance spécifique pour ce service
            date_echeance_str = calculate_service_echeance(service_type, dossier.periode_comptable)
            date_echeance_obj = None
            if date_echeance_str:
                from datetime import datetime as dt2
                date_echeance_obj = dt2.fromisoformat(date_echeance_str).date()
            
            # Générer une référence spécifique pour ce service
            reference = generate_dossier_reference(db, service_type)
            
            # Créer le nouveau dossier
            new_dossier = DossierModel(
                **base_data,
                reference=reference,
                type_dossier=service_type,
                date_echeance=date_echeance_obj,
                services_list=[service_type],  # Un seul service par dossier
                user_id=current_user.id,
                statut=StatusDossier.NOUVEAU
            )
            
            # Calculer la priorité automatiquement
            if new_dossier.date_echeance:
                new_dossier.priorite = new_dossier.priorite_automatique
            
            db.add(new_dossier)
            db.flush()  # Pour obtenir l'ID
            
            
            created_dossiers.append(new_dossier)
            
            # Ajouter à l'historique pour le nouveau dossier
            historique_new = HistoriqueDossier(
                dossier_id=new_dossier.id,
                user_id=current_user.id,
                action="creation",
                new_value=new_dossier.statut.value,
                commentaire=f"Dossier {service_type} créé automatiquement lors de la modification des services"
            )
            db.add(historique_new)
    
    # Ajouter à l'historique pour le dossier modifié
    historique = HistoriqueDossier(
        dossier_id=dossier_id,
        user_id=current_user.id,
        action="update",
        commentaire=f"Dossier mis à jour. {len(created_dossiers)} nouveau(x) dossier(s) créé(s)" if created_dossiers else "Dossier mis à jour"
    )
    db.add(historique)
    
    db.commit()
    db.refresh(dossier)
    
    return dossier


@router.put("/{dossier_id}/status", response_model=Dossier)
async def update_dossier_status(
    dossier_id: int,
    status_update: DossierStatusUpdate,
    current_user: User = Depends(get_current_user),
    cabinet_id: int = Depends(get_current_cabinet_id),
    db: Session = Depends(get_db)
):
    dossier = db.query(DossierModel).filter(
        DossierModel.id == dossier_id,
        DossierModel.cabinet_id == cabinet_id
    ).first()
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")
    
    # VÉRIFICATION DES PERMISSIONS
    if current_user.role == "collaborateur":
        from app.models.client import Client
        clients_assignes = db.query(Client).filter(Client.user_id == current_user.id).all()
        noms_clients = [client.nom for client in clients_assignes]
        
        if dossier.nom_client not in noms_clients:
            raise HTTPException(status_code=403, detail="Accès refusé : ce client ne vous est pas assigné")
    
    old_status = dossier.statut
    dossier.statut = status_update.statut
    dossier.updated_at = datetime.utcnow()
    
    if status_update.statut == StatusDossier.COMPLETE:
        dossier.completed_at = datetime.utcnow()
    
    # Ajouter à l'historique
    historique = HistoriqueDossier(
        dossier_id=dossier_id,
        user_id=current_user.id,
        action="manual_status_change",
        old_value=old_status.value,
        new_value=status_update.statut.value,
        commentaire=status_update.commentaire or "Changement manuel de statut"
    )
    db.add(historique)
    
    db.commit()
    db.refresh(dossier)
    
    return dossier


@router.put("/{dossier_id}/complete", response_model=Dossier)
async def complete_dossier(
    dossier_id: int,
    current_user: User = Depends(get_current_user),
    cabinet_id: int = Depends(get_current_cabinet_id),
    db: Session = Depends(get_db)
):
    """Marque un dossier comme complété"""
    dossier = db.query(DossierModel).filter(
        DossierModel.id == dossier_id,
        DossierModel.cabinet_id == cabinet_id
    ).first()
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")
    
    # VÉRIFICATION DES PERMISSIONS
    if current_user.role == "collaborateur":
        from app.models.client import Client
        clients_assignes = db.query(Client).filter(Client.user_id == current_user.id).all()
        noms_clients = [client.nom for client in clients_assignes]
        
        if dossier.nom_client not in noms_clients:
            raise HTTPException(status_code=403, detail="Accès refusé : ce client ne vous est pas assigné")
    
    if not dossier.peut_passer_complete():
        raise HTTPException(status_code=400, detail="Ce dossier ne peut pas être marqué comme complété")
    
    old_status = dossier.statut
    dossier.statut = StatusDossier.COMPLETE
    dossier.completed_at = datetime.utcnow()
    dossier.updated_at = datetime.utcnow()
    
    # Ajouter à l'historique
    historique = HistoriqueDossier(
        dossier_id=dossier_id,
        user_id=current_user.id,
        action="completion",
        old_value=old_status.value,
        new_value=StatusDossier.COMPLETE.value,
        commentaire="Dossier marqué comme complété"
    )
    db.add(historique)
    
    db.commit()
    db.refresh(dossier)
    
    return dossier


@router.get("/{dossier_id}/documents-requis")
async def get_documents_requis(
    dossier_id: int,
    echeance_id: int = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupérer les documents requis pour un dossier"""
    # Vérifier que le dossier existe
    dossier = db.query(DossierModel).filter(
        DossierModel.id == dossier_id
    ).first()
    
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")
    
    # Vérifier les permissions pour les collaborateurs
    if current_user.role == "collaborateur":
        from app.models.client import Client
        clients_assignes = db.query(Client).filter(Client.user_id == current_user.id).all()
        noms_clients = [client.nom for client in clients_assignes]
        
        if dossier.nom_client not in noms_clients:
            raise HTTPException(status_code=403, detail="Accès refusé")
    
    # Importer les modèles nécessaires
    from app.models.document_requis import DocumentRequis
    from app.models.document import Document
    
    # Construire la requête de base
    query = db.query(DocumentRequis).filter(DocumentRequis.dossier_id == dossier_id)
    
    # Filtrer par échéance si spécifié
    if echeance_id:
        query = query.filter(DocumentRequis.echeance_id == echeance_id)
    
    # Récupérer les documents requis
    documents_requis = query.all()
    
    # Enrichir chaque document requis avec les informations du document fourni s'il existe
    result = []
    for doc_requis in documents_requis:
        # Chercher le document fourni correspondant
        document_fourni = db.query(Document).filter(
            and_(
                Document.dossier_id == dossier_id,
                Document.type == doc_requis.type_document,
                Document.mois == doc_requis.mois,
                Document.annee == doc_requis.annee
            )
        ).first()
        
        # Construire la réponse
        doc_data = {
            "id": doc_requis.id,
            "type_document": doc_requis.type_document.value,
            "mois": doc_requis.mois,
            "annee": doc_requis.annee,
            "est_applicable": doc_requis.est_applicable,
            "est_fourni": document_fourni is not None,
            "document": None
        }
        
        # Ajouter les informations du document fourni s'il existe
        if document_fourni:
            doc_data["document"] = {
                "id": document_fourni.id,
                "nom": document_fourni.nom,
                "url": document_fourni.url or f"/api/v1/documents/{document_fourni.id}/download",
                "created_at": document_fourni.created_at.isoformat()
            }
        
        result.append(doc_data)
    
    logger.info(f"{len(result)} documents requis trouvés pour dossier {dossier_id}")
    return result


@router.get("/{dossier_id}/echeances")
async def get_dossier_echeances(
    dossier_id: int,
    current_user: User = Depends(get_current_user),
    cabinet_id: int = Depends(get_current_cabinet_id),
    db: Session = Depends(get_db)
):
    """Récupérer toutes les échéances d'un dossier avec leurs saisies"""
    # Vérifier que le dossier existe et que l'utilisateur y a accès
    dossier = db.query(DossierModel).filter(
        DossierModel.id == dossier_id,
        DossierModel.cabinet_id == cabinet_id
    ).first()
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")
    
    # Vérifier les permissions
    if current_user.role == "collaborateur":
        from app.models.client import Client
        clients_assignes = db.query(Client).filter(Client.user_id == current_user.id).all()
        noms_clients = [client.nom for client in clients_assignes]
        
        if dossier.nom_client not in noms_clients:
            raise HTTPException(status_code=403, detail="Accès refusé")
    
    # Récupérer les échéances avec leurs saisies
    from app.models.echeance import Echeance
    from app.models.saisie import SaisieComptable
    echeances = db.query(Echeance).filter(
        Echeance.dossier_id == dossier_id
    ).order_by(Echeance.mois).all()
    
    # Enrichir avec les saisies
    result = []
    for echeance in echeances:
        echeance_dict = {
            "id": echeance.id,
            "mois": echeance.mois,
            "annee": echeance.annee,
            "periode_label": echeance.periode_label,
            "date_echeance": echeance.date_echeance,
            "statut": echeance.statut,
            "date_debut": echeance.date_debut,
            "date_completion": echeance.date_completion,
            "notes": echeance.notes,
            "saisies": []
        }
        
        # Récupérer les saisies pour cette échéance
        saisies = db.query(SaisieComptable).filter(
            SaisieComptable.echeance_id == echeance.id
        ).all()
        
        for saisie in saisies:
            echeance_dict["saisies"].append({
                "id": saisie.id,
                "type_journal": saisie.type_journal,
                "est_complete": saisie.est_complete,
                "date_completion": saisie.date_completion
            })
        
        result.append(echeance_dict)
    
    return result


@router.put("/saisies/{saisie_id}")
async def update_saisie(
    saisie_id: int,
    est_complete: bool,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mettre à jour le statut d'une saisie comptable"""
    from app.models.saisie import SaisieComptable
    from app.models.echeance import Echeance
    
    saisie = db.query(SaisieComptable).filter(SaisieComptable.id == saisie_id).first()
    if not saisie:
        raise HTTPException(status_code=404, detail="Saisie non trouvée")
    
    # Vérifier l'accès via le dossier
    dossier = saisie.dossier
    if current_user.role == "collaborateur":
        from app.models.client import Client
        clients_assignes = db.query(Client).filter(Client.user_id == current_user.id).all()
        noms_clients = [client.nom for client in clients_assignes]
        
        if dossier.nom_client not in noms_clients:
            raise HTTPException(status_code=403, detail="Accès refusé")
    
    # Mettre à jour la saisie
    saisie.est_complete = est_complete
    if est_complete:
        saisie.date_completion = datetime.utcnow()
        saisie.completed_by_id = current_user.id
    else:
        saisie.date_completion = None
        saisie.completed_by_id = None
    
    db.commit()
    
    # Vérifier si toutes les saisies de l'échéance sont complètes
    toutes_saisies = db.query(SaisieComptable).filter(
        SaisieComptable.echeance_id == saisie.echeance_id
    ).all()
    
    toutes_completes = all(s.est_complete for s in toutes_saisies)
    
    # Mettre à jour l'échéance si toutes les saisies sont complètes
    echeance = db.query(Echeance).filter(Echeance.id == saisie.echeance_id).first()
    if echeance:
        if toutes_completes and echeance.statut != 'COMPLETE':
            echeance.statut = 'COMPLETE'
            echeance.date_completion = datetime.utcnow()
        elif not toutes_completes and echeance.statut == 'COMPLETE':
            echeance.statut = 'A_FAIRE'
            echeance.date_completion = None
        db.commit()
    
    # Mettre à jour le statut du dossier selon l'avancement global
    if dossier:
        # Vérifier toutes les échéances du dossier
        toutes_echeances = db.query(Echeance).filter(Echeance.dossier_id == dossier.id).all()
        
        if toutes_echeances:
            echeances_completes = sum(1 for e in toutes_echeances if e.statut == 'COMPLETE')
            total_echeances = len(toutes_echeances)
            
            # Logique de mise à jour du statut du dossier
            if echeances_completes == 0 and dossier.statut == StatusDossier.NOUVEAU:
                # On reste en NOUVEAU tant qu'aucune échéance n'est commencée
                pass
            elif echeances_completes > 0 and echeances_completes < total_echeances:
                # Au moins une échéance complète mais pas toutes = EN_COURS
                if dossier.statut != StatusDossier.EN_COURS:
                    dossier.statut = StatusDossier.EN_COURS
                    dossier.updated_at = datetime.utcnow()
            elif echeances_completes == total_echeances:
                # Toutes les échéances sont complètes = COMPLETE
                if dossier.statut != StatusDossier.COMPLETE:
                    dossier.statut = StatusDossier.COMPLETE
                    dossier.completed_at = datetime.utcnow()
                    dossier.updated_at = datetime.utcnow()
        
        # Pour FISCALITE, vérifier aussi les déclarations
        elif dossier.type_dossier == 'FISCALITE':
            from app.models.declaration_fiscale import DeclarationFiscale
            declarations = db.query(DeclarationFiscale).filter(DeclarationFiscale.dossier_id == dossier.id).all()
            if declarations:
                declarations_completes = sum(1 for d in declarations if d.statut in ['TELEDECLAREE', 'VALIDEE'])
                total_declarations = len(declarations)
                
                if declarations_completes > 0 and declarations_completes < total_declarations:
                    if dossier.statut != StatusDossier.EN_COURS:
                        dossier.statut = StatusDossier.EN_COURS
                        dossier.updated_at = datetime.utcnow()
                elif declarations_completes == total_declarations:
                    if dossier.statut != StatusDossier.COMPLETE:
                        dossier.statut = StatusDossier.COMPLETE
                        dossier.completed_at = datetime.utcnow()
                        dossier.updated_at = datetime.utcnow()
        
        # Charger les relations pour calculer correctement la priorité
        db.refresh(dossier)
        
        # Mettre à jour la priorité selon les échéances et tâches en retard
        dossier.priorite = dossier.priorite_automatique
        
        db.commit()
    
    return {"success": True, "toutes_completes": toutes_completes}


@router.post("/{dossier_id}/documents/upload")
async def upload_documents(
    dossier_id: int,
    files: List[UploadFile] = File(...),
    type: Optional[str] = Form(None),
    echeance_id: Optional[int] = Form(None),
    mois: Optional[int] = Form(None),
    annee: Optional[int] = Form(None),
    current_user: User = Depends(get_current_user),
    cabinet_id: int = Depends(get_current_cabinet_id),
    db: Session = Depends(get_db)
):
    """Uploader plusieurs documents pour un dossier avec validation sécurisée"""
    # Vérifier l'accès au dossier
    dossier = db.query(DossierModel).filter(
        DossierModel.id == dossier_id,
        DossierModel.cabinet_id == cabinet_id
    ).first()
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")
    
    if current_user.role == "collaborateur":
        from app.models.client import Client
        clients_assignes = db.query(Client).filter(Client.user_id == current_user.id).all()
        noms_clients = [client.nom for client in clients_assignes]
        
        if dossier.nom_client not in noms_clients:
            raise HTTPException(status_code=403, detail="Accès refusé")
    
    from app.models.document import Document, TypeDocument
    from app.models.document_requis import DocumentRequis
    from app.core.file_validator import file_validator
    import os
    import aiofiles
    import uuid
    
    # Créer le répertoire de stockage s'il n'existe pas
    upload_dir = f"uploads/dossiers/{dossier_id}"
    os.makedirs(upload_dir, exist_ok=True)
    
    uploaded_docs = []
    security_logger = logging.getLogger('security')
    
    try:
        for file in files:
            # Valider le fichier avec notre validateur sécurisé
            safe_filename, mime_type, file_size = await file_validator.validate_file(
                file, 
                check_content=True
            )
            
            # Log de sécurité
            security_logger.info(
                f"File upload validated",
                extra={
                    'user_id': current_user.id,
                    'dossier_id': dossier_id,
                    'original_filename': file.filename,
                    'safe_filename': safe_filename,
                    'mime_type': mime_type,
                    'size': file_size
                }
            )
            
            # Chemin de stockage sécurisé
            file_path = os.path.join(upload_dir, safe_filename)
            
            # Sauvegarder le fichier de manière asynchrone
            async with aiofiles.open(file_path, 'wb') as buffer:
                content = await file.read()
                await buffer.write(content)
            
            # Calculer le hash du fichier pour l'intégrité
            file_hash = file_validator.calculate_file_hash(file_path)
            
            # Créer l'enregistrement en base de données
            document = Document(
                nom=file.filename,  # Nom original pour l'affichage
                nom_fichier_stockage=safe_filename,  # Nom sécurisé pour le stockage
                type=TypeDocument[type] if type else TypeDocument.AUTRE,
                chemin_fichier=file_path,
                url=f"/api/v1/documents/{dossier_id}/{safe_filename}",
                taille=file_size,
                mime_type=mime_type,
                hash_fichier=file_hash,
                dossier_id=dossier_id,
                echeance_id=echeance_id,
                user_id=current_user.id,
                mois=mois,
                annee=annee
            )
            db.add(document)
            db.flush()
            
            uploaded_docs.append({
                "id": document.id,
                "nom": document.nom,
                "type": document.type.value,
                "url": document.url,
                "taille": document.taille,
                "mime_type": document.mime_type
            })
            
            # Marquer le document requis comme fourni si applicable
            if echeance_id and type:
                doc_requis = db.query(DocumentRequis).filter(
                    DocumentRequis.echeance_id == echeance_id,
                    DocumentRequis.type_document == type,
                    DocumentRequis.mois == mois,
                    DocumentRequis.annee == annee
                ).first()
                
                if doc_requis:
                    doc_requis.est_fourni = True
        
        db.commit()
        
        # Log de succès
        security_logger.info(
            f"Files uploaded successfully",
            extra={
                'user_id': current_user.id,
                'dossier_id': dossier_id,
                'file_count': len(uploaded_docs)
            }
        )
        
        return uploaded_docs
        
    except Exception as e:
        # En cas d'erreur, supprimer les fichiers déjà uploadés
        for doc in uploaded_docs:
            try:
                if os.path.exists(doc.get('file_path', '')):
                    os.remove(doc['file_path'])
            except:
                pass
        
        # Log de l'erreur
        security_logger.error(
            f"File upload failed",
            extra={
                'user_id': current_user.id,
                'dossier_id': dossier_id,
                'error': str(e)
            }
        )
        
        raise


@router.get("/{dossier_id}/documents")
async def get_dossier_documents(
    dossier_id: int,
    current_user: User = Depends(get_current_user),
    cabinet_id: int = Depends(get_current_cabinet_id),
    db: Session = Depends(get_db)
):
    """Récupérer tous les documents d'un dossier"""
    # Vérifier l'accès au dossier
    dossier = db.query(DossierModel).filter(
        DossierModel.id == dossier_id,
        DossierModel.cabinet_id == cabinet_id
    ).first()
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")
    
    if current_user.role == "collaborateur":
        from app.models.client import Client
        clients_assignes = db.query(Client).filter(Client.user_id == current_user.id).all()
        noms_clients = [client.nom for client in clients_assignes]
        
        if dossier.nom_client not in noms_clients:
            raise HTTPException(status_code=403, detail="Accès refusé")
    
    # TODO: Récupérer les vrais documents depuis la base de données
    # Pour l'instant, on retourne une liste vide
    return []


@router.get("/{dossier_id}/timeline")
async def get_dossier_timeline(
    dossier_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # TODO: Récupérer l'historique complet d'un dossier
    return {
        "dossier_id": dossier_id,
        "events": []
    }


@router.delete("/{dossier_id}")
async def delete_dossier(
    dossier_id: int,
    current_user: User = Depends(get_current_user),
    cabinet_id: int = Depends(get_current_cabinet_id),
    db: Session = Depends(get_db)
):
    """Supprimer un dossier"""
    dossier = db.query(DossierModel).filter(
        DossierModel.id == dossier_id,
        DossierModel.cabinet_id == cabinet_id
    ).first()
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")
    
    # VÉRIFICATION DES PERMISSIONS
    if current_user.role == "collaborateur":
        # Les collaborateurs ne peuvent supprimer que les dossiers de leurs clients
        from app.models.client import Client
        clients_assignes = db.query(Client).filter(Client.user_id == current_user.id).all()
        noms_clients = [client.nom for client in clients_assignes]
        
        if dossier.nom_client not in noms_clients:
            raise HTTPException(status_code=403, detail="Accès refusé : ce client ne vous est pas assigné")
    
    # Suppression en cascade complète - ordre important pour respecter les contraintes FK
    
    # 1. Supprimer les saisies comptables (dépendent d'échéances et de dossier)
    from app.models.saisie import SaisieComptable
    saisies = db.query(SaisieComptable).filter(SaisieComptable.dossier_id == dossier_id).all()
    for saisie in saisies:
        db.delete(saisie)
    
    # 2. Supprimer les documents requis (dépendent d'échéances et de dossier)
    from app.models.document_requis import DocumentRequis
    docs_requis = db.query(DocumentRequis).filter(DocumentRequis.dossier_id == dossier_id).all()
    for doc in docs_requis:
        db.delete(doc)
    
    # 3. Supprimer les documents (dépendent d'échéances et de dossier)
    from app.models.document import Document
    documents = db.query(Document).filter(Document.dossier_id == dossier_id).all()
    for document in documents:
        db.delete(document)
    
    # 4. Supprimer les notifications liées aux alertes du dossier
    from app.models.notification import Notification
    from app.models.alerte import Alerte
    alertes = db.query(Alerte).filter(Alerte.dossier_id == dossier_id).all()
    for alerte in alertes:
        notifications = db.query(Notification).filter(Notification.alerte_id == alerte.id).all()
        for notification in notifications:
            db.delete(notification)
        db.delete(alerte)
    
    # 5. Supprimer l'historique du dossier
    from app.models.historique import HistoriqueDossier
    historiques = db.query(HistoriqueDossier).filter(HistoriqueDossier.dossier_id == dossier_id).all()
    for historique in historiques:
        db.delete(historique)
    
    # 6. Supprimer les déclarations fiscales
    from app.models.declaration_fiscale import DeclarationFiscale
    declarations = db.query(DeclarationFiscale).filter(DeclarationFiscale.dossier_id == dossier_id).all()
    for declaration in declarations:
        db.delete(declaration)
    
    # 7. Supprimer le dossier (les échéances seront supprimées automatiquement grâce à cascade)
    db.delete(dossier)
    db.commit()
    
    return {"message": f"Dossier {dossier.reference} supprimé avec succès"}



@router.put("/documents-requis/{doc_requis_id}/applicable")
async def update_document_requis_applicable(
    doc_requis_id: int,
    est_applicable: bool,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marquer un document requis comme applicable ou non applicable"""
    from app.models.document_requis import DocumentRequis
    
    doc_requis = db.query(DocumentRequis).filter(DocumentRequis.id == doc_requis_id).first()
    if not doc_requis:
        raise HTTPException(status_code=404, detail="Document requis non trouvé")
    
    # Vérifier l'accès via le dossier
    dossier = doc_requis.dossier
    if current_user.role == "collaborateur":
        from app.models.client import Client
        clients_assignes = db.query(Client).filter(Client.user_id == current_user.id).all()
        noms_clients = [client.nom for client in clients_assignes]
        
        if dossier.nom_client not in noms_clients:
            raise HTTPException(status_code=403, detail="Accès refusé")
    
    # Mettre à jour le statut
    doc_requis.est_applicable = est_applicable
    db.commit()
    
    # Créer une alerte si un document applicable n'est pas fourni
    if est_applicable and not doc_requis.est_fourni:
        alerte_service = AlerteService(db)
        alerte_service.creer_alerte_document_manquant(
            dossier_id=dossier.id,
            type_document=doc_requis.type_document.value,
            echeance_id=doc_requis.echeance_id
        )
    
    return {"success": True, "est_applicable": est_applicable}


@router.get("/{dossier_id}/declarations-fiscales")
async def get_declarations_fiscales(
    dossier_id: int,
    current_user: User = Depends(get_current_user),
    cabinet_id: int = Depends(get_current_cabinet_id),
    db: Session = Depends(get_db)
):
    """Récupérer les déclarations fiscales d'un dossier"""
    from app.models.declaration_fiscale import DeclarationFiscale
    from app.models.client import Client
    
    # Vérifier l'accès au dossier
    dossier = db.query(DossierModel).filter(
        DossierModel.id == dossier_id,
        DossierModel.cabinet_id == cabinet_id
    ).first()
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")
    
    # Contrôle d'accès selon le rôle
    if current_user.role == "collaborateur":
        clients_assignes = db.query(Client).filter(Client.user_id == current_user.id).all()
        noms_clients = [client.nom for client in clients_assignes]
        
        if dossier.nom_client not in noms_clients:
            raise HTTPException(status_code=403, detail="Accès refusé")
    
    # Récupérer les déclarations fiscales
    declarations = db.query(DeclarationFiscale).filter(
        DeclarationFiscale.dossier_id == dossier_id
    ).order_by(DeclarationFiscale.date_limite).all()
    
    # Enrichir avec les propriétés calculées
    result = []
    for declaration in declarations:
        result.append({
            "id": declaration.id,
            "type_declaration": declaration.type_declaration,
            "statut": declaration.statut,
            "regime": declaration.regime,
            "periode_debut": declaration.periode_debut.isoformat(),
            "periode_fin": declaration.periode_fin.isoformat(),
            "date_limite": declaration.date_limite.isoformat(),
            "montant_base": float(declaration.montant_base) if declaration.montant_base else None,
            "montant_taxe": float(declaration.montant_taxe) if declaration.montant_taxe else None,
            "montant_credit": float(declaration.montant_credit) if declaration.montant_credit else None,
            "montant_a_payer": float(declaration.montant_a_payer) if declaration.montant_a_payer else None,
            "numero_teledeclaration": declaration.numero_teledeclaration,
            "date_teledeclaration": declaration.date_teledeclaration.isoformat() if declaration.date_teledeclaration else None,
            "date_paiement": declaration.date_paiement.isoformat() if declaration.date_paiement else None,
            "formulaire_cerfa": declaration.formulaire_cerfa,
            "observations": declaration.observations,
            "libelle_periode": declaration.libelle_periode,
            "est_en_retard": declaration.est_en_retard,
            "jours_avant_echeance": declaration.jours_avant_echeance,
            "priorite_calculee": declaration.priorite_calculee
        })
    
    return result


@router.put("/{declaration_id}/declarations-fiscales/complete")
async def complete_declaration_fiscale(
    declaration_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marquer une déclaration fiscale comme télédéclarée"""
    from app.models.declaration_fiscale import DeclarationFiscale
    from app.models.client import Client
    from datetime import datetime
    
    # Récupérer la déclaration
    declaration = db.query(DeclarationFiscale).filter(
        DeclarationFiscale.id == declaration_id
    ).first()
    
    if not declaration:
        raise HTTPException(status_code=404, detail="Déclaration non trouvée")
    
    # Vérifier l'accès via le dossier
    dossier = db.query(DossierModel).filter(DossierModel.id == declaration.dossier_id).first()
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")
    
    # Contrôle d'accès selon le rôle
    if current_user.role == "collaborateur":
        clients_assignes = db.query(Client).filter(Client.user_id == current_user.id).all()
        noms_clients = [client.nom for client in clients_assignes]
        
        if dossier.nom_client not in noms_clients:
            raise HTTPException(status_code=403, detail="Accès refusé")
    
    # Basculer entre les statuts
    if declaration.statut in ['TELEDECLAREE', 'VALIDEE']:
        # Remettre à faire
        declaration.statut = 'A_FAIRE'
        declaration.date_teledeclaration = None
        declaration.completed_at = None
    else:
        # Marquer comme télédéclarée
        declaration.statut = 'TELEDECLAREE'
        declaration.date_teledeclaration = datetime.now()
        declaration.completed_at = datetime.now()
    
    db.commit()
    
    # Mettre à jour le statut du dossier selon l'avancement global
    if dossier:
        # Vérifier toutes les déclarations du dossier
        toutes_declarations = db.query(DeclarationFiscale).filter(
            DeclarationFiscale.dossier_id == dossier.id
        ).all()
        
        if toutes_declarations:
            declarations_completes = sum(1 for d in toutes_declarations if d.statut in ['TELEDECLAREE', 'VALIDEE'])
            total_declarations = len(toutes_declarations)
            
            # Logique de mise à jour du statut du dossier
            if declarations_completes == 0 and dossier.statut == StatusDossier.NOUVEAU:
                # On reste en NOUVEAU tant qu'aucune déclaration n'est commencée
                pass
            elif declarations_completes > 0 and declarations_completes < total_declarations:
                # Au moins une déclaration complète mais pas toutes = EN_COURS
                if dossier.statut != StatusDossier.EN_COURS:
                    dossier.statut = StatusDossier.EN_COURS
                    dossier.updated_at = datetime.utcnow()
            elif declarations_completes == total_declarations:
                # Toutes les déclarations sont complètes = COMPLETE
                if dossier.statut != StatusDossier.COMPLETE:
                    dossier.statut = StatusDossier.COMPLETE
                    dossier.completed_at = datetime.utcnow()
                    dossier.updated_at = datetime.utcnow()
        
        # Charger les relations pour calculer correctement la priorité
        db.refresh(dossier)
        
        # Mettre à jour la priorité selon les échéances et tâches en retard
        dossier.priorite = dossier.priorite_automatique
        
        db.commit()
    
    return {"success": True, "statut": declaration.statut}