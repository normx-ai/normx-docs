"""add refresh and 2fa tables

Revision ID: add_refresh_and_2fa
Revises: add_security_fields
Create Date: 2025-07-15

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_refresh_and_2fa'
down_revision = 'add_security_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Table pour les refresh tokens
    op.create_table('refresh_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('device_id', sa.String(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked', sa.Boolean(), default=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_refresh_token_token', 'refresh_tokens', ['token'], unique=True)
    op.create_index('idx_refresh_token_user_active', 'refresh_tokens', ['user_id', 'revoked'])
    op.create_index('idx_refresh_token_expires', 'refresh_tokens', ['expires_at'])
    
    # Table pour l'authentification à deux facteurs
    op.create_table('two_factor_auth',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('secret', sa.String(), nullable=False),
        sa.Column('backup_codes', sa.String(), nullable=True),
        sa.Column('enabled', sa.Boolean(), default=False),
        sa.Column('activated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )


def downgrade():
    op.drop_table('two_factor_auth')
    op.drop_index('idx_refresh_token_expires', 'refresh_tokens')
    op.drop_index('idx_refresh_token_user_active', 'refresh_tokens')
    op.drop_index('idx_refresh_token_token', 'refresh_tokens')
    op.drop_table('refresh_tokens')