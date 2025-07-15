"""replace_responsable_with_user_in_clients

Revision ID: a3bbd70c9391
Revises: 0ee653fb6e20
Create Date: 2025-07-12 10:16:45.617714

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3bbd70c9391'
down_revision: Union[str, Sequence[str], None] = '0ee653fb6e20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Replace responsable_id with user_id in clients table and drop responsables table."""
    
    # 1. Modifier la contrainte de clé étrangère pour dossiers.responsable_id vers users
    op.drop_constraint('dossiers_responsable_id_fkey', 'dossiers', type_='foreignkey')
    op.create_foreign_key(
        'dossiers_responsable_id_fkey',
        'dossiers',
        'users',
        ['responsable_id'],
        ['id']
    )
    
    # 2. Ajouter la colonne user_id à la table clients
    op.add_column('clients', sa.Column('user_id', sa.Integer(), nullable=True))
    
    # 3. Ajouter la contrainte de clé étrangère vers users
    op.create_foreign_key(
        'clients_user_id_fkey',
        'clients',
        'users',
        ['user_id'],
        ['id']
    )
    
    # 4. Supprimer la contrainte de clé étrangère vers responsables
    op.drop_constraint('clients_responsable_id_fkey', 'clients', type_='foreignkey')
    
    # 5. Supprimer la colonne responsable_id de clients
    op.drop_column('clients', 'responsable_id')
    
    # 6. Supprimer la table responsables
    op.drop_table('responsables')


def downgrade() -> None:
    """Restore responsables table and responsable_id in clients."""
    
    # 1. Recréer la table responsables
    op.create_table('responsables',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nom', sa.String(), nullable=False),
        sa.Column('prenom', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('telephone', sa.String(), nullable=True),
        sa.Column('fonction', sa.String(), nullable=True),
        sa.Column('specialites', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_responsables_email', 'responsables', ['email'], unique=True)
    op.create_index('ix_responsables_id', 'responsables', ['id'], unique=False)
    
    # 2. Ajouter la colonne responsable_id à clients
    op.add_column('clients', sa.Column('responsable_id', sa.Integer(), nullable=True))
    
    # 3. Ajouter la contrainte de clé étrangère vers responsables
    op.create_foreign_key(
        'clients_responsable_id_fkey',
        'clients',
        'responsables',
        ['responsable_id'],
        ['id']
    )
    
    # 4. Supprimer la contrainte vers users
    op.drop_constraint('clients_user_id_fkey', 'clients', type_='foreignkey')
    
    # 5. Supprimer la colonne user_id
    op.drop_column('clients', 'user_id')
