"""add_site_web_to_user

Revision ID: ab1122e2df61
Revises: 0400d4095fce
Create Date: 2025-07-12 09:31:53.469651

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ab1122e2df61'
down_revision: Union[str, Sequence[str], None] = '0400d4095fce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add site_web column to users table."""
    op.add_column('users', sa.Column('site_web', sa.String(), nullable=True))


def downgrade() -> None:
    """Remove site_web column from users table."""
    op.drop_column('users', 'site_web')
