#!/usr/bin/env python3

# Lire le fichier
with open('/home/chris/gd-ia-comptable/app/api/users.py', 'r') as f:
    lines = f.readlines()

# Trouver et remplacer les lignes problématiques
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # Fix cabinet settings function body
    if 'cabinet.nom = settings.cabinet_name' in line and i > 0:
        # Nous devons remplacer toute la fonction jusqu'à return current_user
        # Reculer pour trouver le début
        j = i
        while j > 0 and '"""Mettre à jour les paramètres du cabinet"""' not in lines[j]:
            j -= 1
        
        # Remplacer depuis le début de la fonction
        if j > 0:
            # Garder les lignes avant
            new_lines = new_lines[:len(new_lines) - (i - j)]
            
            # Ajouter le nouveau code
            new_lines.append('    """Mettre à jour les paramètres du cabinet"""\n')
            new_lines.append('    # Récupérer le cabinet\n')
            new_lines.append('    from app.models.cabinet import Cabinet\n')
            new_lines.append('    cabinet = db.query(Cabinet).filter(Cabinet.id == cabinet_id).first()\n')
            new_lines.append('    if not cabinet:\n')
            new_lines.append('        raise HTTPException(status_code=404, detail="Cabinet non trouvé")\n')
            new_lines.append('    \n')
            new_lines.append('    # Mettre à jour les champs fournis sur le cabinet\n')
            new_lines.append('    if settings.cabinet_name is not None:\n')
            new_lines.append('        cabinet.nom = settings.cabinet_name\n')
            new_lines.append('    if settings.siret is not None:\n')
            new_lines.append('        cabinet.siret = settings.siret\n')
            new_lines.append('    if settings.siren is not None:\n')
            new_lines.append('        cabinet.siren = settings.siren\n')
            new_lines.append('    if settings.nom_gerant is not None:\n')
            new_lines.append('        current_user.nom_gerant = settings.nom_gerant\n')
            new_lines.append('    if settings.adresse_cabinet is not None:\n')
            new_lines.append('        cabinet.adresse = settings.adresse_cabinet\n')
            new_lines.append('    if settings.code_postal is not None:\n')
            new_lines.append('        cabinet.code_postal = settings.code_postal\n')
            new_lines.append('    if settings.ville is not None:\n')
            new_lines.append('        cabinet.ville = settings.ville\n')
            new_lines.append('    if settings.telephone_cabinet is not None:\n')
            new_lines.append('        cabinet.telephone = settings.telephone_cabinet\n')
            new_lines.append('    if settings.email_cabinet is not None:\n')
            new_lines.append('        cabinet.email = settings.email_cabinet\n')
            new_lines.append('    if settings.site_web is not None:\n')
            new_lines.append('        current_user.site_web = settings.site_web\n')
            new_lines.append('    \n')
            new_lines.append('    db.commit()\n')
            new_lines.append('    db.refresh(current_user)\n')
            new_lines.append('    db.refresh(cabinet)\n')
            new_lines.append('    \n')
            new_lines.append('    return current_user\n')
            
            # Avancer jusqu'à la fin de la fonction
            while i < len(lines) and 'return current_user' not in lines[i]:
                i += 1
            i += 1
            continue
    
    # Nettoyer "No newline at end of file"
    if "No newline at end of file" in line:
        line = line.replace(" No newline at end of file", "")
    
    new_lines.append(line)
    i += 1

# Écrire le fichier
with open('/home/chris/gd-ia-comptable/app/api/users.py', 'w') as f:
    f.writelines(new_lines)

print("✅ API users corrigée avec succès !")