"""add_localization_fields_to_cabinet

Revision ID: 501cbc3402a6
Revises: multi_tenant_001
Create Date: 2025-07-12 23:22:48.401858

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '501cbc3402a6'
down_revision: Union[str, Sequence[str], None] = 'multi_tenant_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Ajouter les champs de localisation
    op.add_column('cabinets', sa.Column('pays_code', sa.String(length=2), nullable=False, server_default='FR'))
    op.add_column('cabinets', sa.Column('langue', sa.String(length=5), nullable=False, server_default='fr-FR'))
    op.add_column('cabinets', sa.Column('fuseau_horaire', sa.String(length=50), nullable=False, server_default='Europe/Paris'))
    op.add_column('cabinets', sa.Column('devise', sa.String(length=3), nullable=False, server_default='EUR'))
    op.add_column('cabinets', sa.Column('format_date', sa.String(length=20), nullable=False, server_default='DD/MM/YYYY'))


def downgrade() -> None:
    """Downgrade schema."""
    # Supprimer les champs de localisation
    op.drop_column('cabinets', 'format_date')
    op.drop_column('cabinets', 'devise')
    op.drop_column('cabinets', 'fuseau_horaire')
    op.drop_column('cabinets', 'langue')
    op.drop_column('cabinets', 'pays_code')
