"""fix_responsable_foreign_key

Revision ID: 37337360e626
Revises: a3bbd70c9391
Create Date: 2025-07-12 11:52:24.480860

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '37337360e626'
down_revision: Union[str, Sequence[str], None] = 'a3bbd70c9391'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Supprimer l'ancienne contrainte de foreign key vers responsables
    op.drop_constraint('dossiers_responsable_id_fkey', 'dossiers', type_='foreignkey')
    
    # Créer la nouvelle contrainte vers la table users
    op.create_foreign_key(
        'dossiers_responsable_id_fkey', 
        'dossiers', 
        'users',
        ['responsable_id'], 
        ['id']
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Supprimer la contrainte vers users
    op.drop_constraint('dossiers_responsable_id_fkey', 'dossiers', type_='foreignkey')
    
    # Recréer l'ancienne contrainte vers responsables (si la table existe)
    op.create_foreign_key(
        'dossiers_responsable_id_fkey', 
        'dossiers', 
        'responsables',
        ['responsable_id'], 
        ['id']
    )
