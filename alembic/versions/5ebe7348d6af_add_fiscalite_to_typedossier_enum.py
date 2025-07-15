"""Add FISCALITE to TypeDossier enum

Revision ID: 5ebe7348d6af
Revises: 25099789407d
Create Date: 2025-07-12 14:11:06.857963

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5ebe7348d6af'
down_revision: Union[str, Sequence[str], None] = '25099789407d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Ajouter FISCALITE à l'enum typedossier
    op.execute("ALTER TYPE typedossier ADD VALUE IF NOT EXISTS 'FISCALITE'")


def downgrade() -> None:
    """Downgrade schema."""
    # Note: PostgreSQL ne permet pas de supprimer des valeurs d'enum facilement
    # Il faudrait recréer l'enum entièrement pour le rollback
    pass
