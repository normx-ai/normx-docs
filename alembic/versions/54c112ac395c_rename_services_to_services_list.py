"""rename_services_to_services_list

Revision ID: 54c112ac395c
Revises: 83388593c54a
Create Date: 2025-07-12 07:58:08.941824

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '54c112ac395c'
down_revision: Union[str, Sequence[str], None] = '83388593c54a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Renommer la colonne services en services_list
    op.alter_column('dossiers', 'services', new_column_name='services_list')


def downgrade() -> None:
    """Downgrade schema."""
    # Renommer la colonne services_list en services
    op.alter_column('dossiers', 'services_list', new_column_name='services')
