"""add security fields to documents

Revision ID: add_security_fields
Revises: f3ad6a9dde9d
Create Date: 2025-07-15

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_security_fields'
down_revision = 'f3ad6a9dde9d'
branch_labels = None
depends_on = None


def upgrade():
    # Ajouter les nouveaux champs de sécurité
    op.add_column('documents', sa.Column('nom_fichier_stockage', sa.String(), nullable=True))
    op.add_column('documents', sa.Column('mime_type', sa.String(), nullable=True))
    op.add_column('documents', sa.Column('hash_fichier', sa.String(), nullable=True))
    
    # Remplir nom_fichier_stockage avec le nom existant pour les documents existants
    op.execute("UPDATE documents SET nom_fichier_stockage = nom WHERE nom_fichier_stockage IS NULL")
    
    # Rendre nom_fichier_stockage non nullable
    op.alter_column('documents', 'nom_fichier_stockage', nullable=False)
    
    # Créer un index sur le hash pour vérifier les doublons
    op.create_index('idx_documents_hash', 'documents', ['hash_fichier'])


def downgrade():
    op.drop_index('idx_documents_hash', 'documents')
    op.drop_column('documents', 'hash_fichier')
    op.drop_column('documents', 'mime_type')
    op.drop_column('documents', 'nom_fichier_stockage')