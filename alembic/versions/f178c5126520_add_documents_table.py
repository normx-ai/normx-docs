"""add_documents_table

Revision ID: f178c5126520
Revises: 710b39225e64
Create Date: 2025-07-12 12:35:34.616632

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f178c5126520'
down_revision: Union[str, Sequence[str], None] = '710b39225e64'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Ajouter simplement les colonnes manquantes si nécessaire
    # Pour l'instant on laisse la table documents telle quelle
    # car elle existe déjà avec une structure différente
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass