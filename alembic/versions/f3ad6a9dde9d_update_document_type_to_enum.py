"""update_document_type_to_enum

Revision ID: f3ad6a9dde9d
Revises: c506d7926a71
Create Date: 2025-07-12 12:56:30.243550

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f3ad6a9dde9d'
down_revision: Union[str, Sequence[str], None] = 'c506d7926a71'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Créer le type enum
    typedocument = postgresql.ENUM(
        'FACTURE_ACHAT', 'RELEVE_BANCAIRE', 'FACTURE_VENTE', 
        'ETAT_PAIE', 'DECLARATION_IMPOT', 'DECLARATION_TVA',
        'DECLARATION_SOCIALE', 'CONTRAT', 'COURRIER', 'AUTRE',
        name='typedocument'
    )
    typedocument.create(op.get_bind())
    
    # Ajouter une colonne temporaire
    op.add_column('documents', sa.Column('type_new', sa.Enum(
        'FACTURE_ACHAT', 'RELEVE_BANCAIRE', 'FACTURE_VENTE', 
        'ETAT_PAIE', 'DECLARATION_IMPOT', 'DECLARATION_TVA',
        'DECLARATION_SOCIALE', 'CONTRAT', 'COURRIER', 'AUTRE',
        name='typedocument'
    ), nullable=True))
    
    # Migrer les données existantes
    connection = op.get_bind()
    result = connection.execute(sa.text("SELECT DISTINCT type FROM documents WHERE type IS NOT NULL"))
    existing_types = [row[0] for row in result]
    
    # Mapper les anciens types vers les nouveaux
    type_mapping = {
        'facture_achat': 'FACTURE_ACHAT',
        'releve_bancaire': 'RELEVE_BANCAIRE',
        'facture_vente': 'FACTURE_VENTE',
        'etat_paie': 'ETAT_PAIE',
        'declaration_impot': 'DECLARATION_IMPOT',
        'declaration_tva': 'DECLARATION_TVA',
        'declaration_sociale': 'DECLARATION_SOCIALE',
        'contrat': 'CONTRAT',
        'courrier': 'COURRIER'
    }
    
    for old_type in existing_types:
        new_type = type_mapping.get(old_type.lower(), 'AUTRE')
        connection.execute(
            sa.text("UPDATE documents SET type_new = :new_type WHERE type = :old_type"),
            {"new_type": new_type, "old_type": old_type}
        )
    
    # Mettre à jour les valeurs NULL
    connection.execute(sa.text("UPDATE documents SET type_new = 'AUTRE' WHERE type IS NULL"))
    
    # Supprimer l'ancienne colonne et renommer la nouvelle
    op.drop_column('documents', 'type')
    op.alter_column('documents', 'type_new', new_column_name='type', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Ajouter une colonne temporaire
    op.add_column('documents', sa.Column('type_old', sa.String(), nullable=True))
    
    # Migrer les données
    connection = op.get_bind()
    connection.execute(sa.text("UPDATE documents SET type_old = type::text"))
    
    # Supprimer l'ancienne colonne et renommer la nouvelle
    op.drop_column('documents', 'type')
    op.alter_column('documents', 'type_old', new_column_name='type', nullable=True)
    
    # Supprimer le type enum
    typedocument = postgresql.ENUM(name='typedocument')
    typedocument.drop(op.get_bind())
