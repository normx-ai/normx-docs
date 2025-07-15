#!/usr/bin/env python3
"""
Script pour créer une migration Alembic pour le multi-tenant
"""

import subprocess
import os
import time

def create_migration():
    print("=== Création de la migration multi-tenant ===")
    
    # Se placer dans le répertoire du projet
    os.chdir('/home/chris/gd-ia-comptable')
    
    # Créer la migration
    timestamp = int(time.time())
    migration_name = f"add_multi_tenant_support_{timestamp}"
    
    cmd = [
        "venv/bin/alembic", 
        "revision", 
        "--autogenerate", 
        "-m", 
        migration_name
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        print("Sortie:", result.stdout)
        if result.stderr:
            print("Erreurs:", result.stderr)
        
        if result.returncode == 0:
            print(f"✅ Migration créée avec succès: {migration_name}")
            # Trouver le fichier de migration créé
            migrations_dir = "alembic/versions"
            for filename in os.listdir(migrations_dir):
                if migration_name in filename:
                    print(f"📄 Fichier de migration: {migrations_dir}/{filename}")
                    return os.path.join(migrations_dir, filename)
        else:
            print("❌ Erreur lors de la création de la migration")
            return None
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None

if __name__ == "__main__":
    create_migration()