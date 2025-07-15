#!/usr/bin/env python3
"""
Script pour corriger l'API users avec le filtrage par cabinet_id
"""

# Lire le fichier
with open('/home/chris/gd-ia-comptable/app/api/users.py', 'r') as f:
    content = f.read()

# Dans update_user (ligne 168)
old_update = """    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # Les managers ne peuvent pas modifier les admins"""

new_update = """    user = db.query(UserModel).filter(
        UserModel.id == user_id,
        UserModel.cabinet_id == cabinet_id
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # Les managers ne peuvent pas modifier les admins"""

content = content.replace(old_update, new_update)

# Dans toggle_user_active (ligne 206)
old_toggle = """    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # Ne pas permettre de désactiver son propre compte"""

new_toggle = """    user = db.query(UserModel).filter(
        UserModel.id == user_id,
        UserModel.cabinet_id == cabinet_id
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # Ne pas permettre de désactiver son propre compte"""

content = content.replace(old_toggle, new_toggle)

# Dans delete_user - ajouter le filtre cabinet_id
old_delete_query = """    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # Ne pas permettre de supprimer son propre compte"""

new_delete_query = """    user = db.query(UserModel).filter(
        UserModel.id == user_id,
        UserModel.cabinet_id == cabinet_id
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # Ne pas permettre de supprimer son propre compte"""

content = content.replace(old_delete_query, new_delete_query)

# Vérifier aussi le cabinet settings
old_cabinet_settings = """@router.put("/cabinet-settings", response_model=User)
async def update_cabinet_settings(
    settings: CabinetSettings,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):"""

new_cabinet_settings = """@router.put("/cabinet-settings", response_model=User)
async def update_cabinet_settings(
    settings: CabinetSettings,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
    cabinet_id: int = Depends(get_current_cabinet_id)
):"""

content = content.replace(old_cabinet_settings, new_cabinet_settings)

# Sauvegarder le fichier
with open('/home/chris/gd-ia-comptable/app/api/users.py', 'w') as f:
    f.write(content)

print("✅ API users mise à jour avec succès !")