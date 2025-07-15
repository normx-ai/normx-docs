"""add_client_fields_forme_juridique_gerant

Revision ID: eb099eb32c0a
Revises: 54c112ac395c
Create Date: 2025-07-12 08:08:45.459317

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eb099eb32c0a'
down_revision: Union[str, Sequence[str], None] = '54c112ac395c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Ajouter les nouvelles colonnes
    op.add_column('clients', sa.Column('forme_juridique', sa.String(), nullable=True))
    op.add_column('clients', sa.Column('nom_gerant', sa.String(), nullable=True))
    op.add_column('clients', sa.Column('telephone_gerant', sa.String(), nullable=True))
    op.add_column('clients', sa.Column('email_gerant', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Supprimer les colonnes
    op.drop_column('clients', 'email_gerant')
    op.drop_column('clients', 'telephone_gerant')
    op.drop_column('clients', 'nom_gerant')
    op.drop_column('clients', 'forme_juridique')
