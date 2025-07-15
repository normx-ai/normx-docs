"""add_echeances_table

Revision ID: 710b39225e64
Revises: 37337360e626
Create Date: 2025-07-12 12:07:56.569935

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '710b39225e64'
down_revision: Union[str, Sequence[str], None] = '37337360e626'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create echeances table
    op.create_table(
        'echeances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dossier_id', sa.Integer(), nullable=False),
        sa.Column('mois', sa.Integer(), nullable=False),
        sa.Column('annee', sa.Integer(), nullable=False),
        sa.Column('periode_label', sa.String(), nullable=False),
        sa.Column('date_echeance', sa.Date(), nullable=False),
        sa.Column('statut', sa.String(), nullable=True),
        sa.Column('date_debut', sa.DateTime(timezone=True), nullable=True),
        sa.Column('date_completion', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['dossier_id'], ['dossiers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_echeances_date_echeance'), 'echeances', ['date_echeance'], unique=False)
    op.create_index(op.f('ix_echeances_id'), 'echeances', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_echeances_id'), table_name='echeances')
    op.drop_index(op.f('ix_echeances_date_echeance'), table_name='echeances')
    op.drop_table('echeances')
