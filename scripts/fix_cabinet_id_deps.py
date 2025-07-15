#!/usr/bin/env python3
"""
Script pour corriger les dépendances cabinet_id manquantes
"""

import re

# Lire le fichier
with open('/home/chris/gd-ia-comptable/app/api/dossiers.py', 'r') as f:
    content = f.read()

# Liste des fonctions qui ont besoin de cabinet_id
functions_needing_cabinet_id = [
    ('get_dossier', '@router.get("/{dossier_id}", response_model=Dossier)'),
    ('update_dossier', '@router.put("/{dossier_id}", response_model=Dossier)'),
    ('update_dossier_status', '@router.put("/{dossier_id}/status", response_model=Dossier)'),
    ('complete_dossier', '@router.put("/{dossier_id}/complete", response_model=Dossier)'),
    ('get_dossier_echeances', '@router.get("/{dossier_id}/echeances")'),
    ('upload_documents', '@router.post("/{dossier_id}/documents/upload")'),
    ('get_dossier_documents', '@router.get("/{dossier_id}/documents")'),
    ('get_timeline', '@router.get("/{dossier_id}/timeline")'),
    ('delete_dossier', '@router.delete("/{dossier_id}")'),
    ('get_declarations_fiscales', '@router.get("/{dossier_id}/declarations-fiscales")'),
]

# Pour chaque fonction, ajouter cabinet_id dans les paramètres
for func_name, decorator in functions_needing_cabinet_id:
    # Trouver la fonction
    pattern = f'{re.escape(decorator)}\nasync def {func_name}\(([^)]+)\):'
    match = re.search(pattern, content)
    
    if match:
        params = match.group(1)
        # Si cabinet_id n'est pas déjà dans les paramètres
        if 'cabinet_id' not in params:
            # Ajouter cabinet_id avant la parenthèse fermante
            new_params = params.rstrip() + ',\n    cabinet_id: int = Depends(get_current_cabinet_id)'
            new_func_def = f'{decorator}\nasync def {func_name}({new_params}):'
            content = content.replace(match.group(0), new_func_def)
            print(f"✅ Ajouté cabinet_id à {func_name}")

# Corriger l'endpoint get_documents_requis
old_get_docs_requis = """@router.get("/{dossier_id}/documents-requis")
async def get_documents_requis(
    dossier_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):"""

new_get_docs_requis = """@router.get("/{dossier_id}/documents-requis")
async def get_documents_requis(
    dossier_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    cabinet_id: int = Depends(get_current_cabinet_id)
):"""

content = content.replace(old_get_docs_requis, new_get_docs_requis)

# Ajouter le filtre cabinet_id dans get_documents_requis
old_docs_requis_query = """    # Vérifier l'accès au dossier
    dossier = db.query(DossierModel).filter(DossierModel.id == dossier_id).first()"""

new_docs_requis_query = """    # Vérifier l'accès au dossier
    dossier = db.query(DossierModel).filter(
        DossierModel.id == dossier_id,
        DossierModel.cabinet_id == cabinet_id
    ).first()"""

content = content.replace(old_docs_requis_query, new_docs_requis_query)

# Corriger l'endpoint update_saisie
old_update_saisie = """@router.put("/saisies/{saisie_id}")
async def update_saisie(
    saisie_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):"""

new_update_saisie = """@router.put("/saisies/{saisie_id}")
async def update_saisie(
    saisie_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    cabinet_id: int = Depends(get_current_cabinet_id)
):"""

content = content.replace(old_update_saisie, new_update_saisie)

# Ajouter le filtre cabinet_id dans update_saisie
old_saisie_query = """    # Vérifier que la saisie existe et récupérer le dossier associé
    saisie = db.query(SaisieComptable).filter(SaisieComptable.id == saisie_id).first()
    if not saisie:
        raise HTTPException(status_code=404, detail="Saisie non trouvée")
    
    # Récupérer le dossier pour vérifier les permissions
    dossier = db.query(DossierModel).filter(DossierModel.id == saisie.dossier_id).first()"""

new_saisie_query = """    # Vérifier que la saisie existe et appartient au cabinet
    saisie = db.query(SaisieComptable).filter(
        SaisieComptable.id == saisie_id,
        SaisieComptable.cabinet_id == cabinet_id
    ).first()
    if not saisie:
        raise HTTPException(status_code=404, detail="Saisie non trouvée")
    
    # Récupérer le dossier pour vérifier les permissions
    dossier = db.query(DossierModel).filter(
        DossierModel.id == saisie.dossier_id,
        DossierModel.cabinet_id == cabinet_id
    ).first()"""

content = content.replace(old_saisie_query, new_saisie_query)

# Corriger l'endpoint update_document_requis_applicable
old_update_doc_requis = """@router.put("/documents-requis/{doc_requis_id}/applicable")
async def update_document_requis_applicable(
    doc_requis_id: int,
    applicable: bool,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):"""

new_update_doc_requis = """@router.put("/documents-requis/{doc_requis_id}/applicable")
async def update_document_requis_applicable(
    doc_requis_id: int,
    applicable: bool,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    cabinet_id: int = Depends(get_current_cabinet_id)
):"""

content = content.replace(old_update_doc_requis, new_update_doc_requis)

# Ajouter le filtre cabinet_id dans update_document_requis_applicable
old_doc_requis_applicable_query = """    # Récupérer le document requis
    doc_requis = db.query(DocumentRequis).filter(DocumentRequis.id == doc_requis_id).first()
    if not doc_requis:
        raise HTTPException(status_code=404, detail="Document requis non trouvé")
    
    # Vérifier les permissions via le dossier
    dossier = db.query(DossierModel).filter(DossierModel.id == doc_requis.dossier_id).first()"""

new_doc_requis_applicable_query = """    # Récupérer le document requis
    doc_requis = db.query(DocumentRequis).filter(
        DocumentRequis.id == doc_requis_id,
        DocumentRequis.cabinet_id == cabinet_id
    ).first()
    if not doc_requis:
        raise HTTPException(status_code=404, detail="Document requis non trouvé")
    
    # Vérifier les permissions via le dossier
    dossier = db.query(DossierModel).filter(
        DossierModel.id == doc_requis.dossier_id,
        DossierModel.cabinet_id == cabinet_id
    ).first()"""

content = content.replace(old_doc_requis_applicable_query, new_doc_requis_applicable_query)

# Corriger l'endpoint update_declaration_complete
old_update_declaration = """@router.put("/{declaration_id}/declarations-fiscales/complete")
async def update_declaration_complete(
    declaration_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):"""

new_update_declaration = """@router.put("/{declaration_id}/declarations-fiscales/complete")
async def update_declaration_complete(
    declaration_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    cabinet_id: int = Depends(get_current_cabinet_id)
):"""

content = content.replace(old_update_declaration, new_update_declaration)

# Ajouter le filtre cabinet_id dans update_declaration_complete
old_declaration_query = """    # Récupérer la déclaration
    declaration = db.query(DeclarationFiscale).filter(DeclarationFiscale.id == declaration_id).first()
    if not declaration:
        raise HTTPException(status_code=404, detail="Déclaration non trouvée")
    
    # Vérifier l'accès au dossier
    dossier = db.query(DossierModel).filter(DossierModel.id == declaration.dossier_id).first()"""

new_declaration_query = """    # Récupérer la déclaration
    declaration = db.query(DeclarationFiscale).filter(
        DeclarationFiscale.id == declaration_id,
        DeclarationFiscale.cabinet_id == cabinet_id
    ).first()
    if not declaration:
        raise HTTPException(status_code=404, detail="Déclaration non trouvée")
    
    # Vérifier l'accès au dossier
    dossier = db.query(DossierModel).filter(
        DossierModel.id == declaration.dossier_id,
        DossierModel.cabinet_id == cabinet_id
    ).first()"""

content = content.replace(old_declaration_query, new_declaration_query)

# Corriger les appels à generate_dossier_reference
# Premier appel dans create_echeances_paie
old_call1 = 'dossier_data["reference"] = generate_dossier_reference(db, service_type)'
new_call1 = 'dossier_data["reference"] = generate_dossier_reference(db, service_type, cabinet_id)'
content = content.replace(old_call1, new_call1)

# Deuxième appel dans update_dossier
old_call2 = 'dossier.reference = generate_dossier_reference(db, service_type)'
new_call2 = 'dossier.reference = generate_dossier_reference(db, service_type, cabinet_id)'
content = content.replace(old_call2, new_call2)

# Sauvegarder le fichier
with open('/home/chris/gd-ia-comptable/app/api/dossiers.py', 'w') as f:
    f.write(content)

print("✅ Toutes les dépendances cabinet_id ont été corrigées !")