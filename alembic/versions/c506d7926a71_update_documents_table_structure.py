"""update_documents_table_structure

Revision ID: c506d7926a71
Revises: ceae736841ab
Create Date: 2025-07-12 13:11:11.072525

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c506d7926a71'
down_revision: Union[str, Sequence[str], None] = 'ceae736841ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Ajouter les nouvelles colonnes si elles n'existent pas
    try:
        op.add_column('documents', sa.Column('nom', sa.String(), nullable=True))
    except:
        pass  # La colonne existe déjà
    
    try:
        op.add_column('documents', sa.Column('type', sa.String(), nullable=True))
    except:
        pass
    
    try:
        op.add_column('documents', sa.Column('chemin_fichier', sa.String(), nullable=True))
    except:
        pass
    
    try:
        op.add_column('documents', sa.Column('url', sa.String(), nullable=True))
    except:
        pass
    
    try:
        op.add_column('documents', sa.Column('taille', sa.Integer(), nullable=True))
    except:
        pass
    
    try:
        op.add_column('documents', sa.Column('echeance_id', sa.Integer(), nullable=True))
    except:
        pass
    
    try:
        op.add_column('documents', sa.Column('user_id', sa.Integer(), nullable=True))
    except:
        pass
    
    try:
        op.add_column('documents', sa.Column('mois', sa.Integer(), nullable=True))
    except:
        pass
    
    try:
        op.add_column('documents', sa.Column('annee', sa.Integer(), nullable=True))
    except:
        pass
    
    # Ajouter les foreign keys si elles n'existent pas
    try:
        op.create_foreign_key('fk_documents_echeance', 'documents', 'echeances', ['echeance_id'], ['id'])
    except:
        pass
    
    try:
        op.create_foreign_key('fk_documents_user', 'documents', 'users', ['user_id'], ['id'])
    except:
        pass
    
    # Migrer les données existantes si nécessaire
    connection = op.get_bind()
    
    # Vérifier si la colonne filename existe et copier vers nom
    result = connection.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='documents' AND column_name='filename'
    """))
    if result.fetchone():
        connection.execute(sa.text("""
            UPDATE documents 
            SET nom = filename 
            WHERE nom IS NULL AND filename IS NOT NULL
        """))
    
    # Vérifier si la colonne type_document existe et copier vers type
    result = connection.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='documents' AND column_name='type_document'
    """))
    if result.fetchone():
        connection.execute(sa.text("""
            UPDATE documents 
            SET type = type_document 
            WHERE type IS NULL AND type_document IS NOT NULL
        """))
    
    # Vérifier si la colonne file_path existe et copier vers chemin_fichier
    result = connection.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='documents' AND column_name='file_path'
    """))
    if result.fetchone():
        connection.execute(sa.text("""
            UPDATE documents 
            SET chemin_fichier = file_path 
            WHERE chemin_fichier IS NULL AND file_path IS NOT NULL
        """))
    
    # Vérifier si la colonne uploaded_by_id existe et copier vers user_id
    result = connection.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='documents' AND column_name='uploaded_by_id'
    """))
    if result.fetchone():
        connection.execute(sa.text("""
            UPDATE documents 
            SET user_id = uploaded_by_id 
            WHERE user_id IS NULL AND uploaded_by_id IS NOT NULL
        """))


def downgrade() -> None:
    """Downgrade schema."""
    # Supprimer les foreign keys
    try:
        op.drop_constraint('fk_documents_echeance', 'documents', type_='foreignkey')
    except:
        pass
    
    try:
        op.drop_constraint('fk_documents_user', 'documents', type_='foreignkey')
    except:
        pass
    
    # Supprimer les colonnes ajoutées
    try:
        op.drop_column('documents', 'nom')
    except:
        pass
    
    try:
        op.drop_column('documents', 'type')
    except:
        pass
    
    try:
        op.drop_column('documents', 'chemin_fichier')
    except:
        pass
    
    try:
        op.drop_column('documents', 'url')
    except:
        pass
    
    try:
        op.drop_column('documents', 'taille')
    except:
        pass
    
    try:
        op.drop_column('documents', 'echeance_id')
    except:
        pass
    
    try:
        op.drop_column('documents', 'user_id')
    except:
        pass
    
    try:
        op.drop_column('documents', 'mois')
    except:
        pass
    
    try:
        op.drop_column('documents', 'annee')
    except:
        pass