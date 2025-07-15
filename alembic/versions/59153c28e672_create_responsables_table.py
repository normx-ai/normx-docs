"""create_responsables_table

Revision ID: 59153c28e672
Revises: eb099eb32c0a
Create Date: 2025-07-12 08:57:34.314655

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '59153c28e672'
down_revision: Union[str, Sequence[str], None] = 'eb099eb32c0a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Créer la table responsables
    op.create_table('responsables',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nom', sa.String(), nullable=False),
        sa.Column('prenom', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('telephone', sa.String(), nullable=True),
        sa.Column('fonction', sa.String(), nullable=True),
        sa.Column('specialites', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_responsables_email'), 'responsables', ['email'], unique=True)
    op.create_index(op.f('ix_responsables_id'), 'responsables', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_responsables_id'), table_name='responsables')
    op.drop_index(op.f('ix_responsables_email'), table_name='responsables')
    op.drop_table('responsables')
