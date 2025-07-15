#!/usr/bin/env python3
"""
Script pour mettre à jour l'API dossiers avec le filtrage par cabinet_id
"""

import re

# Lire le fichier
with open('/home/chris/gd-ia-comptable/app/api/dossiers.py', 'r') as f:
    content = f.read()

# Modifications à apporter

# 1. Endpoint POST /
old_post = """@router.post("/", response_model=dict)
async def create_dossier(
    dossier: DossierCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):"""

new_post = """@router.post("/", response_model=dict)
async def create_dossier(
    dossier: DossierCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    cabinet_id: int = Depends(get_current_cabinet_id)
):"""

content = content.replace(old_post, new_post)

# 2. Dans create_dossier, ajouter cabinet_id
old_create = """    # Générer une référence automatique si non fournie
    if not dossier_data.get('reference'):
        dossier_data['reference'] = generate_dossier_reference(db, dossier.type_dossier)
    
    # Ajouter l'utilisateur qui crée le dossier
    dossier_data['user_id'] = current_user.id"""

new_create = """    # Générer une référence automatique si non fournie
    if not dossier_data.get('reference'):
        dossier_data['reference'] = generate_dossier_reference(db, dossier.type_dossier, cabinet_id)
    
    # Ajouter l'utilisateur qui crée le dossier et le cabinet
    dossier_data['user_id'] = current_user.id
    dossier_data['cabinet_id'] = cabinet_id"""

content = content.replace(old_create, new_create)

# 3. Endpoint GET /
old_get_all = """@router.get("/", response_model=List[DossierWithDetails])
async def list_dossiers(
    skip: int = 0,
    limit: int = 100,
    type_dossier: Optional[TypeDossier] = None,
    statut: Optional[StatusDossier] = None,
    search: Optional[str] = None,
    sort_by: str = Query("date_echeance", regex="^(date_echeance|nom_client|reference|statut|priorite)$"),
    sort_desc: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):"""

new_get_all = """@router.get("/", response_model=List[DossierWithDetails])
async def list_dossiers(
    skip: int = 0,
    limit: int = 100,
    type_dossier: Optional[TypeDossier] = None,
    statut: Optional[StatusDossier] = None,
    search: Optional[str] = None,
    sort_by: str = Query("date_echeance", regex="^(date_echeance|nom_client|reference|statut|priorite)$"),
    sort_desc: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    cabinet_id: int = Depends(get_current_cabinet_id)
):"""

content = content.replace(old_get_all, new_get_all)

# 4. Dans list_dossiers, ajouter le filtre cabinet_id
old_query = """    # Commencer la requête avec les filtres basiques selon le rôle
    if current_user.role == "admin":
        query = db.query(DossierModel)
    elif current_user.role == "manager":
        query = db.query(DossierModel)
    else:
        # Collaborateur voit uniquement ses dossiers ou ceux où il est responsable
        query = db.query(DossierModel).filter(
            or_(
                DossierModel.user_id == current_user.id,
                DossierModel.responsable_id == current_user.id
            )
        )"""

new_query = """    # Commencer la requête avec les filtres basiques selon le rôle et le cabinet
    base_query = db.query(DossierModel).filter(DossierModel.cabinet_id == cabinet_id)
    
    if current_user.role == "admin":
        query = base_query
    elif current_user.role == "manager":
        query = base_query
    else:
        # Collaborateur voit uniquement ses dossiers ou ceux où il est responsable
        query = base_query.filter(
            or_(
                DossierModel.user_id == current_user.id,
                DossierModel.responsable_id == current_user.id
            )
        )"""

content = content.replace(old_query, new_query)

# 5. Endpoint GET /daily-point
old_daily = """@router.get("/daily-point", response_model=DailyPoint)
async def get_daily_point(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):"""

new_daily = """@router.get("/daily-point", response_model=DailyPoint)
async def get_daily_point(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    cabinet_id: int = Depends(get_current_cabinet_id)
):"""

content = content.replace(old_daily, new_daily)

# 6. Dans get_daily_point, ajouter le filtre cabinet_id
old_daily_query = """    # Filtrer les dossiers selon le rôle de l'utilisateur
    if current_user.role == "admin":
        dossiers = db.query(DossierModel).all()
    elif current_user.role == "manager":
        dossiers = db.query(DossierModel).all()
    else:
        # Collaborateur voit uniquement ses dossiers
        dossiers = db.query(DossierModel).filter(
            or_(
                DossierModel.user_id == current_user.id,
                DossierModel.responsable_id == current_user.id
            )
        ).all()"""

new_daily_query = """    # Filtrer les dossiers selon le rôle de l'utilisateur et le cabinet
    base_query = db.query(DossierModel).filter(DossierModel.cabinet_id == cabinet_id)
    
    if current_user.role == "admin":
        dossiers = base_query.all()
    elif current_user.role == "manager":
        dossiers = base_query.all()
    else:
        # Collaborateur voit uniquement ses dossiers
        dossiers = base_query.filter(
            or_(
                DossierModel.user_id == current_user.id,
                DossierModel.responsable_id == current_user.id
            )
        ).all()"""

content = content.replace(old_daily_query, new_daily_query)

# 7. Endpoint GET /stats/echeances
old_stats = """@router.get("/stats/echeances")
async def get_echeances_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):"""

new_stats = """@router.get("/stats/echeances")
async def get_echeances_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    cabinet_id: int = Depends(get_current_cabinet_id)
):"""

content = content.replace(old_stats, new_stats)

# 8. Dans get_echeances_stats, ajouter le filtre cabinet_id
old_stats_query = """    # Récupérer tous les dossiers actifs
    dossiers_query = db.query(DossierModel).filter(
        DossierModel.statut != StatusDossier.ARCHIVE
    )"""

new_stats_query = """    # Récupérer tous les dossiers actifs du cabinet
    dossiers_query = db.query(DossierModel).filter(
        DossierModel.cabinet_id == cabinet_id,
        DossierModel.statut != StatusDossier.ARCHIVE
    )"""

content = content.replace(old_stats_query, new_stats_query)

# 9. Endpoint GET /{dossier_id}
old_get_one = """@router.get("/{dossier_id}", response_model=Dossier)
async def get_dossier(
    dossier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):"""

new_get_one = """@router.get("/{dossier_id}", response_model=Dossier)
async def get_dossier(
    dossier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    cabinet_id: int = Depends(get_current_cabinet_id)
):"""

content = content.replace(old_get_one, new_get_one)

# 10. Dans get_dossier, vérifier le cabinet_id
old_get_check = """    dossier = db.query(DossierModel).filter(DossierModel.id == dossier_id).first()
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")"""

new_get_check = """    dossier = db.query(DossierModel).filter(
        DossierModel.id == dossier_id,
        DossierModel.cabinet_id == cabinet_id
    ).first()
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")"""

content = content.replace(old_get_check, new_get_check)

# Sauvegarder le fichier
with open('/home/chris/gd-ia-comptable/app/api/dossiers.py', 'w') as f:
    f.write(content)

print("✅ Fichier dossiers.py mis à jour avec succès !")