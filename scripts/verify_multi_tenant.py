#!/usr/bin/env python3
"""
Script pour vérifier que toutes les APIs sont correctement configurées pour le multi-tenant
"""

import os
import re

def check_api_file(filepath):
    """Vérifie qu'un fichier API est correctement configuré"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    issues = []
    
    # Vérifier l'import de get_current_cabinet_id
    if 'get_current_cabinet_id' not in content:
        issues.append("❌ Import de get_current_cabinet_id manquant")
    
    # Trouver tous les endpoints
    endpoints = re.findall(r'@router\.(get|post|put|delete|patch)\("([^"]+)"\).*?\nasync def (\w+)', content, re.DOTALL)
    
    for method, path, func_name in endpoints:
        # Chercher la définition de la fonction
        func_pattern = f'async def {func_name}\([^)]+\):'
        func_match = re.search(func_pattern, content)
        
        if func_match:
            func_def = func_match.group(0)
            
            # Vérifier si c'est un endpoint qui devrait avoir cabinet_id
            # Exclure les endpoints de login/token
            if 'token' not in path and 'login' not in path and 'cabinet_id' not in func_def:
                issues.append(f"⚠️  Endpoint {method.upper()} {path} ({func_name}) pourrait avoir besoin de cabinet_id")
    
    return issues

def main():
    print("=== Vérification de la configuration multi-tenant ===\n")
    
    api_dir = '/home/chris/gd-ia-comptable/app/api'
    
    # Liste des fichiers API à vérifier
    api_files = [
        'users.py',
        'clients.py', 
        'dossiers.py',
        # Ajouter d'autres fichiers API si nécessaire
    ]
    
    all_good = True
    
    for api_file in api_files:
        filepath = os.path.join(api_dir, api_file)
        if os.path.exists(filepath):
            print(f"\n📄 Vérification de {api_file}:")
            issues = check_api_file(filepath)
            
            if issues:
                all_good = False
                for issue in issues:
                    print(f"   {issue}")
            else:
                print("   ✅ Tout semble correct")
        else:
            print(f"\n❌ Fichier {api_file} non trouvé")
            all_good = False
    
    # Vérifier la base de données
    print("\n📊 Vérification de la base de données:")
    try:
        import sys
        sys.path.append('/home/chris/gd-ia-comptable')
        from sqlalchemy import create_engine, inspect
        from app.core.config import settings
        
        engine = create_engine(settings.DATABASE_URL)
        inspector = inspect(engine)
        
        # Vérifier que la table cabinets existe
        tables = inspector.get_table_names()
        if 'cabinets' in tables:
            print("   ✅ Table 'cabinets' existe")
            
            # Vérifier les colonnes cabinet_id dans les autres tables
            tables_to_check = ['users', 'clients', 'dossiers', 'documents', 'echeances', 
                             'alertes', 'historique_dossiers', 'notifications', 
                             'saisies_comptables', 'documents_requis', 'declarations_fiscales']
            
            for table in tables_to_check:
                if table in tables:
                    columns = [col['name'] for col in inspector.get_columns(table)]
                    if 'cabinet_id' in columns:
                        print(f"   ✅ Table '{table}' a la colonne cabinet_id")
                    else:
                        print(f"   ❌ Table '{table}' n'a PAS de colonne cabinet_id")
                        all_good = False
        else:
            print("   ❌ Table 'cabinets' n'existe pas!")
            all_good = False
            
    except Exception as e:
        print(f"   ❌ Erreur lors de la vérification de la base: {e}")
        all_good = False
    
    print("\n" + "="*50)
    if all_good:
        print("✅ La configuration multi-tenant semble correcte!")
    else:
        print("❌ Des problèmes ont été détectés. Veuillez les corriger.")

if __name__ == "__main__":
    main()