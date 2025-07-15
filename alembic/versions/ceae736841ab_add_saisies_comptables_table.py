"""add_saisies_comptables_table

Revision ID: ceae736841ab
Revises: f178c5126520
Create Date: 2025-07-12 12:40:44.291313

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ceae736841ab'
down_revision: Union[str, Sequence[str], None] = 'f178c5126520'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create saisies_comptables table
    op.create_table('saisies_comptables',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dossier_id', sa.Integer(), nullable=False),
        sa.Column('echeance_id', sa.Integer(), nullable=False),
        sa.Column('type_journal', sa.String(), nullable=False),
        sa.Column('est_complete', sa.Boolean(), default=False),
        sa.Column('date_completion', sa.DateTime(timezone=True), nullable=True),
        sa.Column('mois', sa.Integer(), nullable=False),
        sa.Column('annee', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['dossier_id'], ['dossiers.id'], ),
        sa.ForeignKeyConstraint(['echeance_id'], ['echeances.id'], ),
        sa.ForeignKeyConstraint(['completed_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_saisies_comptables_id'), 'saisies_comptables', ['id'], unique=False)
    op.create_index('ix_saisies_comptables_dossier_mois_annee', 'saisies_comptables', ['dossier_id', 'mois', 'annee'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_saisies_comptables_dossier_mois_annee', table_name='saisies_comptables')
    op.drop_index(op.f('ix_saisies_comptables_id'), table_name='saisies_comptables')
    op.drop_table('saisies_comptables')