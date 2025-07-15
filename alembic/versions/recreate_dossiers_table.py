"""Recreate dossiers table with new structure

Revision ID: recreate_dossiers_v2
Revises: 633c3dc229a4
Create Date: 2025-07-11 22:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'recreate_dossiers_v2'
down_revision: Union[str, Sequence[str], None] = '633c3dc229a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the old table
    op.drop_table('dossiers')
    
    # Create new enums
    op.execute("CREATE TYPE statusdossier AS ENUM ('NOUVEAU', 'EN_COURS', 'EN_ATTENTE', 'COMPLETE', 'ARCHIVE')")
    op.execute("CREATE TYPE typedossier AS ENUM ('COMPTABILITE', 'FISCAL', 'PAIE', 'JURIDIQUE', 'AUDIT', 'CONSEIL', 'AUTRE')")
    op.execute("CREATE TYPE prioritedossier AS ENUM ('BASSE', 'NORMALE', 'HAUTE', 'URGENTE')")
    
    # Create the new table
    op.create_table('dossiers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('reference', sa.String(), nullable=False),
        sa.Column('nom_client', sa.String(), nullable=False),
        sa.Column('services', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('type_dossier', sa.Enum('COMPTABILITE', 'FISCAL', 'PAIE', 'JURIDIQUE', 'AUDIT', 'CONSEIL', 'AUTRE', name='typedossier'), nullable=False),
        sa.Column('statut', sa.Enum('NOUVEAU', 'EN_COURS', 'EN_ATTENTE', 'COMPLETE', 'ARCHIVE', name='statusdossier'), nullable=True),
        sa.Column('date_echeance', sa.Date(), nullable=True),
        sa.Column('responsable_id', sa.Integer(), nullable=True),
        sa.Column('priorite', sa.Enum('BASSE', 'NORMALE', 'HAUTE', 'URGENTE', name='prioritedossier'), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('contact_principal', sa.String(), nullable=True),
        sa.Column('telephone', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['responsable_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dossiers_id'), 'dossiers', ['id'], unique=False)
    op.create_index(op.f('ix_dossiers_reference'), 'dossiers', ['reference'], unique=True)
    op.create_index(op.f('ix_dossiers_nom_client'), 'dossiers', ['nom_client'], unique=False)
    op.create_index(op.f('ix_dossiers_date_echeance'), 'dossiers', ['date_echeance'], unique=False)


def downgrade() -> None:
    # Drop the new table
    op.drop_index(op.f('ix_dossiers_date_echeance'), table_name='dossiers')
    op.drop_index(op.f('ix_dossiers_nom_client'), table_name='dossiers')
    op.drop_index(op.f('ix_dossiers_reference'), table_name='dossiers')
    op.drop_index(op.f('ix_dossiers_id'), table_name='dossiers')
    op.drop_table('dossiers')
    
    # Drop enums
    op.execute("DROP TYPE statusdossier")
    op.execute("DROP TYPE typedossier")
    op.execute("DROP TYPE prioritedossier")
    
    # Recreate old table structure
    op.create_table('dossiers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_name', sa.String(), nullable=False),
        sa.Column('type_dossier', sa.Enum('TVA', 'BILAN', 'SOCIAL', 'FISCAL', 'AUTRE', name='typedossier'), nullable=False),
        sa.Column('status', sa.Enum('NOUVEAU', 'EN_COURS', 'EN_ATTENTE', 'COMPLETE', 'ARCHIVE', name='statusdossier'), nullable=True),
        sa.Column('deadline', sa.Date(), nullable=False),
        sa.Column('responsable_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('priorite', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['responsable_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dossiers_id'), 'dossiers', ['id'], unique=False)
    op.create_index(op.f('ix_dossiers_client_name'), 'dossiers', ['client_name'], unique=False)
    op.create_index(op.f('ix_dossiers_deadline'), 'dossiers', ['deadline'], unique=False)