#!/usr/bin/env python3
"""
Script final pour corriger l'API users
"""

# Lire le fichier
with open('/home/chris/gd-ia-comptable/app/api/users.py', 'r') as f:
    content = f.read()

# 1. Endpoint update_user - ajouter cabinet_id dependency
old_update_user = """@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):"""

new_update_user = """@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
    cabinet_id: int = Depends(get_current_cabinet_id)
):"""

content = content.replace(old_update_user, new_update_user)

# 2. Endpoint toggle_user_active - ajouter cabinet_id dependency
old_toggle = """@router.put("/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):"""

new_toggle = """@router.put("/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
    cabinet_id: int = Depends(get_current_cabinet_id)
):"""

content = content.replace(old_toggle, new_toggle)

# 3. Endpoint delete_user - ajouter cabinet_id dependency
old_delete = """@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):"""

new_delete = """@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
    cabinet_id: int = Depends(get_current_cabinet_id)
):"""

content = content.replace(old_delete, new_delete)

# 4. Endpoint get_all_users - ajouter cabinet_id dependency et filtre
old_get_all = """@router.get("/all", response_model=List[User])
async def get_all_users(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtenir tous les utilisateurs (admin/manager uniquement)"""
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=403,
            detail="Permissions insuffisantes"
        )
    
    users = db.query(UserModel).all()
    return users"""

new_get_all = """@router.get("/all", response_model=List[User])
async def get_all_users(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
    cabinet_id: int = Depends(get_current_cabinet_id)
):
    """Obtenir tous les utilisateurs (admin/manager uniquement)"""
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=403,
            detail="Permissions insuffisantes"
        )
    
    users = db.query(UserModel).filter(UserModel.cabinet_id == cabinet_id).all()
    return users"""

content = content.replace(old_get_all, new_get_all)

# 5. Corriger cabinet_name dans update_cabinet_settings
# Cette fonction doit mettre à jour le cabinet, pas l'utilisateur
old_cabinet_settings_body = """    \"\"\"Mettre à jour les paramètres du cabinet\"\"\"
    # Mettre à jour les champs fournis
    if settings.cabinet_name is not None:
        current_user.cabinet_name = settings.cabinet_name
    if settings.siret is not None:
        current_user.siret = settings.siret
    if settings.siren is not None:
        current_user.siren = settings.siren
    if settings.nom_gerant is not None:
        current_user.nom_gerant = settings.nom_gerant
    if settings.adresse_cabinet is not None:
        current_user.adresse_cabinet = settings.adresse_cabinet
    if settings.code_postal is not None:
        current_user.code_postal = settings.code_postal
    if settings.ville is not None:
        current_user.ville = settings.ville
    if settings.telephone_cabinet is not None:
        current_user.telephone_cabinet = settings.telephone_cabinet
    if settings.email_cabinet is not None:
        current_user.email_cabinet = settings.email_cabinet
    if settings.site_web is not None:
        current_user.site_web = settings.site_web
    
    db.commit()
    db.refresh(current_user)
    
    return current_user"""

new_cabinet_settings_body = """    \"\"\"Mettre à jour les paramètres du cabinet\"\"\"
    # Récupérer le cabinet
    from app.models.cabinet import Cabinet
    cabinet = db.query(Cabinet).filter(Cabinet.id == cabinet_id).first()
    if not cabinet:
        raise HTTPException(status_code=404, detail="Cabinet non trouvé")
    
    # Mettre à jour les champs fournis sur le cabinet
    if settings.cabinet_name is not None:
        cabinet.nom = settings.cabinet_name
    if settings.siret is not None:
        cabinet.siret = settings.siret
    if settings.siren is not None:
        cabinet.siren = settings.siren
    if settings.nom_gerant is not None:
        # Ce champ reste sur l'utilisateur
        current_user.nom_gerant = settings.nom_gerant
    if settings.adresse_cabinet is not None:
        cabinet.adresse = settings.adresse_cabinet
    if settings.code_postal is not None:
        cabinet.code_postal = settings.code_postal
    if settings.ville is not None:
        cabinet.ville = settings.ville
    if settings.telephone_cabinet is not None:
        cabinet.telephone = settings.telephone_cabinet
    if settings.email_cabinet is not None:
        cabinet.email = settings.email_cabinet
    if settings.site_web is not None:
        current_user.site_web = settings.site_web
    
    db.commit()
    db.refresh(current_user)
    db.refresh(cabinet)
    
    return current_user"""

content = content.replace(old_cabinet_settings_body, new_cabinet_settings_body)

# Nettoyer les "No newline at end of file"
content = content.replace(" No newline at end of file", "")

# Sauvegarder le fichier
with open('/home/chris/gd-ia-comptable/app/api/users.py', 'w') as f:
    f.write(content)

print("✅ API users corrigée avec succès !")