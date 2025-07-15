"""update_dossier_responsable_foreign_key

Revision ID: 0400d4095fce
Revises: 59153c28e672
Create Date: 2025-07-12 09:03:42.176081

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0400d4095fce'
down_revision: Union[str, Sequence[str], None] = '59153c28e672'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Update responsable_id foreign key from users to responsables table."""
    # Drop the existing foreign key constraint
    op.drop_constraint('dossiers_responsable_id_fkey', 'dossiers', type_='foreignkey')
    
    # Create new foreign key constraint pointing to responsables table
    op.create_foreign_key(
        'dossiers_responsable_id_fkey',
        'dossiers',
        'responsables',
        ['responsable_id'],
        ['id']
    )


def downgrade() -> None:
    """Revert responsable_id foreign key back to users table."""
    # Drop the foreign key constraint
    op.drop_constraint('dossiers_responsable_id_fkey', 'dossiers', type_='foreignkey')
    
    # Create foreign key constraint pointing back to users table
    op.create_foreign_key(
        'dossiers_responsable_id_fkey',
        'dossiers',
        'users',
        ['responsable_id'],
        ['id']
    )
