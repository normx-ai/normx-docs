"""Add client info fields to dossier

Revision ID: 83388593c54a
Revises: 9aded8cf9548
Create Date: 2025-07-11 23:42:55.486489

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '83388593c54a'
down_revision: Union[str, Sequence[str], None] = '9aded8cf9548'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('dossiers', sa.Column('notes', sa.Text(), nullable=True))
    op.add_column('dossiers', sa.Column('type_entreprise', sa.String(), nullable=True))
    op.add_column('dossiers', sa.Column('numero_siret', sa.String(), nullable=True))
    op.add_column('dossiers', sa.Column('periode_comptable', sa.String(), nullable=True))
    op.add_column('dossiers', sa.Column('exercice_fiscal', sa.String(), nullable=True))
    op.add_column('dossiers', sa.Column('contact_client', sa.String(), nullable=True))
    op.add_column('dossiers', sa.Column('telephone_client', sa.String(), nullable=True))
    op.add_column('dossiers', sa.Column('user_id', sa.Integer(), nullable=False))
    op.create_foreign_key(None, 'dossiers', 'users', ['user_id'], ['id'])
    op.drop_column('dossiers', 'telephone')
    op.drop_column('dossiers', 'contact_principal')
    op.drop_column('dossiers', 'email')
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('dossiers', sa.Column('email', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('dossiers', sa.Column('contact_principal', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('dossiers', sa.Column('telephone', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'dossiers', type_='foreignkey')
    op.drop_column('dossiers', 'user_id')
    op.drop_column('dossiers', 'telephone_client')
    op.drop_column('dossiers', 'contact_client')
    op.drop_column('dossiers', 'exercice_fiscal')
    op.drop_column('dossiers', 'periode_comptable')
    op.drop_column('dossiers', 'numero_siret')
    op.drop_column('dossiers', 'type_entreprise')
    op.drop_column('dossiers', 'notes')
    # ### end Alembic commands ###
