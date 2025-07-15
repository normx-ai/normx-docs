"""Create DeclarationFiscale table only

Revision ID: 25099789407d
Revises: 38b4734bdeae
Create Date: 2025-07-12 13:57:28.496752

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '25099789407d'
down_revision: Union[str, Sequence[str], None] = 'a7b0f77399b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Créer la table declarations_fiscales avec des types String pour éviter les conflits d'enums
    op.create_table('declarations_fiscales',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dossier_id', sa.Integer(), nullable=False),
        sa.Column('type_declaration', sa.String(50), nullable=False),
        sa.Column('statut', sa.String(50), nullable=False, default='A_FAIRE'),
        sa.Column('regime', sa.String(50), nullable=False),
        sa.Column('periode_debut', sa.Date(), nullable=False),
        sa.Column('periode_fin', sa.Date(), nullable=False),
        sa.Column('date_limite', sa.Date(), nullable=False),
        sa.Column('montant_base', sa.Numeric(12, 2), nullable=True),
        sa.Column('montant_taxe', sa.Numeric(12, 2), nullable=True),
        sa.Column('montant_credit', sa.Numeric(12, 2), nullable=True),
        sa.Column('montant_a_payer', sa.Numeric(12, 2), nullable=True),
        sa.Column('numero_teledeclaration', sa.String(), nullable=True),
        sa.Column('date_teledeclaration', sa.DateTime(), nullable=True),
        sa.Column('date_paiement', sa.Date(), nullable=True),
        sa.Column('formulaire_cerfa', sa.String(), nullable=True),
        sa.Column('observations', sa.Text(), nullable=True),
        sa.Column('declaration_origine_id', sa.Integer(), nullable=True),
        sa.Column('est_rectificative', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['dossier_id'], ['dossiers.id'], ),
        sa.ForeignKeyConstraint(['declaration_origine_id'], ['declarations_fiscales.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_declarations_fiscales_id'), 'declarations_fiscales', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Supprimer la table
    op.drop_index(op.f('ix_declarations_fiscales_id'), table_name='declarations_fiscales')
    op.drop_table('declarations_fiscales')
