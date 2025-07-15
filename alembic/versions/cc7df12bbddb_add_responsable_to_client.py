"""add_responsable_to_client

Revision ID: cc7df12bbddb
Revises: ab1122e2df61
Create Date: 2025-07-12 10:03:22.766041

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc7df12bbddb'
down_revision: Union[str, Sequence[str], None] = 'ab1122e2df61'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add responsable_id to clients table."""
    # Ajouter la colonne responsable_id
    op.add_column('clients', sa.Column('responsable_id', sa.Integer(), nullable=True))
    
    # Ajouter la contrainte de clé étrangère
    op.create_foreign_key(
        'clients_responsable_id_fkey',
        'clients',
        'responsables',
        ['responsable_id'],
        ['id']
    )


def downgrade() -> None:
    """Remove responsable_id from clients table."""
    # Supprimer la contrainte de clé étrangère
    op.drop_constraint('clients_responsable_id_fkey', 'clients', type_='foreignkey')
    
    # Supprimer la colonne
    op.drop_column('clients', 'responsable_id')
