"""add multi-tenant support

Revision ID: multi_tenant_001
Revises: 5ebe7348d6af
Create Date: 2025-07-12 22:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'multi_tenant_001'
down_revision: Union[str, Sequence[str], None] = '5ebe7348d6af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add multi-tenant support to all tables"""
    
    # 1. Create cabinets table
    op.create_table('cabinets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nom', sa.String(), nullable=False),
        sa.Column('slug', sa.String(), nullable=False),
        sa.Column('siret', sa.String(length=14), nullable=True),
        sa.Column('siren', sa.String(length=9), nullable=True),
        sa.Column('numero_tva', sa.String(), nullable=True),
        sa.Column('adresse', sa.Text(), nullable=True),
        sa.Column('code_postal', sa.String(length=5), nullable=True),
        sa.Column('ville', sa.String(), nullable=True),
        sa.Column('telephone', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('max_users', sa.Integer(), default=5),
        sa.Column('max_clients', sa.Integer(), default=100),
        sa.Column('plan', sa.String(), default='standard'),
        sa.Column('date_expiration', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nom'),
        sa.UniqueConstraint('slug')
    )
    op.create_index(op.f('ix_cabinets_id'), 'cabinets', ['id'], unique=False)
    op.create_index(op.f('ix_cabinets_slug'), 'cabinets', ['slug'], unique=True)
    
    # 2. Insert a default cabinet
    op.execute("""
        INSERT INTO cabinets (nom, slug, is_active, plan, max_users, max_clients)
        VALUES ('Cabinet Principal', 'cabinet-principal', true, 'standard', 10, 1000)
    """)
    
    # Get the default cabinet ID
    connection = op.get_bind()
    result = connection.execute(sa.text("SELECT id FROM cabinets WHERE slug = 'cabinet-principal'"))
    default_cabinet_id = result.scalar()
    
    # 3. Add cabinet_id to users table
    op.add_column('users', sa.Column('cabinet_id', sa.Integer(), nullable=True))
    
    # Set default cabinet_id for existing users
    op.execute(f"UPDATE users SET cabinet_id = {default_cabinet_id}")
    
    # Make cabinet_id NOT NULL
    op.alter_column('users', 'cabinet_id', nullable=False)
    
    # Add foreign key
    op.create_foreign_key('fk_users_cabinet', 'users', 'cabinets', ['cabinet_id'], ['id'])
    
    # Drop unique constraints on username and email
    op.drop_index('ix_users_username', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    
    # Recreate indexes without unique
    op.create_index('ix_users_username', 'users', ['username'], unique=False)
    op.create_index('ix_users_email', 'users', ['email'], unique=False)
    
    # Add unique constraint for cabinet_id + username
    op.create_unique_constraint('uq_user_cabinet_username', 'users', ['cabinet_id', 'username'])
    
    # 4. Add cabinet_id to clients table
    op.add_column('clients', sa.Column('cabinet_id', sa.Integer(), nullable=True))
    op.execute(f"UPDATE clients SET cabinet_id = {default_cabinet_id}")
    op.alter_column('clients', 'cabinet_id', nullable=False)
    op.create_foreign_key('fk_clients_cabinet', 'clients', 'cabinets', ['cabinet_id'], ['id'])
    
    # Drop unique constraint on numero_client if exists
    try:
        op.drop_index('ix_clients_numero_client', table_name='clients')
    except:
        pass
    
    # Recreate index without unique and add composite unique constraint
    op.create_index('ix_clients_numero_client', 'clients', ['numero_client'], unique=False)
    op.create_unique_constraint('uq_client_cabinet_numero', 'clients', ['cabinet_id', 'numero_client'])
    
    # 5. Add cabinet_id to dossiers table
    op.add_column('dossiers', sa.Column('cabinet_id', sa.Integer(), nullable=True))
    op.execute(f"UPDATE dossiers SET cabinet_id = {default_cabinet_id}")
    op.alter_column('dossiers', 'cabinet_id', nullable=False)
    op.create_foreign_key('fk_dossiers_cabinet', 'dossiers', 'cabinets', ['cabinet_id'], ['id'])
    
    # Drop unique constraint on reference if exists
    try:
        op.drop_index('ix_dossiers_reference', table_name='dossiers')
    except:
        pass
    
    # Recreate index without unique and add composite unique constraint
    op.create_index('ix_dossiers_reference', 'dossiers', ['reference'], unique=False)
    op.create_unique_constraint('uq_dossier_cabinet_reference', 'dossiers', ['cabinet_id', 'reference'])
    
    # 6. Add cabinet_id to documents table
    op.add_column('documents', sa.Column('cabinet_id', sa.Integer(), nullable=True))
    op.execute(f"UPDATE documents SET cabinet_id = {default_cabinet_id}")
    op.alter_column('documents', 'cabinet_id', nullable=False)
    op.create_foreign_key('fk_documents_cabinet', 'documents', 'cabinets', ['cabinet_id'], ['id'])
    
    # 7. Add cabinet_id to echeances table
    op.add_column('echeances', sa.Column('cabinet_id', sa.Integer(), nullable=True))
    op.execute(f"UPDATE echeances SET cabinet_id = {default_cabinet_id}")
    op.alter_column('echeances', 'cabinet_id', nullable=False)
    op.create_foreign_key('fk_echeances_cabinet', 'echeances', 'cabinets', ['cabinet_id'], ['id'])
    
    # 8. Add cabinet_id to alertes table
    op.add_column('alertes', sa.Column('cabinet_id', sa.Integer(), nullable=True))
    op.execute(f"UPDATE alertes SET cabinet_id = {default_cabinet_id}")
    op.alter_column('alertes', 'cabinet_id', nullable=False)
    op.create_foreign_key('fk_alertes_cabinet', 'alertes', 'cabinets', ['cabinet_id'], ['id'])
    
    # 9. Add cabinet_id to historique_dossiers table
    op.add_column('historique_dossiers', sa.Column('cabinet_id', sa.Integer(), nullable=True))
    op.execute(f"UPDATE historique_dossiers SET cabinet_id = {default_cabinet_id}")
    op.alter_column('historique_dossiers', 'cabinet_id', nullable=False)
    op.create_foreign_key('fk_historique_cabinet', 'historique_dossiers', 'cabinets', ['cabinet_id'], ['id'])
    
    # 10. Add cabinet_id to notifications table
    op.add_column('notifications', sa.Column('cabinet_id', sa.Integer(), nullable=True))
    op.execute(f"UPDATE notifications SET cabinet_id = {default_cabinet_id}")
    op.alter_column('notifications', 'cabinet_id', nullable=False)
    op.create_foreign_key('fk_notifications_cabinet', 'notifications', 'cabinets', ['cabinet_id'], ['id'])
    
    # 11. Add cabinet_id to saisies_comptables table
    op.add_column('saisies_comptables', sa.Column('cabinet_id', sa.Integer(), nullable=True))
    op.execute(f"UPDATE saisies_comptables SET cabinet_id = {default_cabinet_id}")
    op.alter_column('saisies_comptables', 'cabinet_id', nullable=False)
    op.create_foreign_key('fk_saisies_cabinet', 'saisies_comptables', 'cabinets', ['cabinet_id'], ['id'])
    
    # 12. Add cabinet_id to documents_requis table
    op.add_column('documents_requis', sa.Column('cabinet_id', sa.Integer(), nullable=True))
    op.execute(f"UPDATE documents_requis SET cabinet_id = {default_cabinet_id}")
    op.alter_column('documents_requis', 'cabinet_id', nullable=False)
    op.create_foreign_key('fk_documents_requis_cabinet', 'documents_requis', 'cabinets', ['cabinet_id'], ['id'])
    
    # 13. Add cabinet_id to declarations_fiscales table
    op.add_column('declarations_fiscales', sa.Column('cabinet_id', sa.Integer(), nullable=True))
    op.execute(f"UPDATE declarations_fiscales SET cabinet_id = {default_cabinet_id}")
    op.alter_column('declarations_fiscales', 'cabinet_id', nullable=False)
    op.create_foreign_key('fk_declarations_cabinet', 'declarations_fiscales', 'cabinets', ['cabinet_id'], ['id'])


def downgrade() -> None:
    """Remove multi-tenant support"""
    
    # Drop foreign keys and cabinet_id columns
    op.drop_constraint('fk_declarations_cabinet', 'declarations_fiscales', type_='foreignkey')
    op.drop_column('declarations_fiscales', 'cabinet_id')
    
    op.drop_constraint('fk_documents_requis_cabinet', 'documents_requis', type_='foreignkey')
    op.drop_column('documents_requis', 'cabinet_id')
    
    op.drop_constraint('fk_saisies_cabinet', 'saisies_comptables', type_='foreignkey')
    op.drop_column('saisies_comptables', 'cabinet_id')
    
    op.drop_constraint('fk_notifications_cabinet', 'notifications', type_='foreignkey')
    op.drop_column('notifications', 'cabinet_id')
    
    op.drop_constraint('fk_historique_cabinet', 'historique_dossiers', type_='foreignkey')
    op.drop_column('historique_dossiers', 'cabinet_id')
    
    op.drop_constraint('fk_alertes_cabinet', 'alertes', type_='foreignkey')
    op.drop_column('alertes', 'cabinet_id')
    
    op.drop_constraint('fk_echeances_cabinet', 'echeances', type_='foreignkey')
    op.drop_column('echeances', 'cabinet_id')
    
    op.drop_constraint('fk_documents_cabinet', 'documents', type_='foreignkey')
    op.drop_column('documents', 'cabinet_id')
    
    # Restore unique constraints on dossiers
    op.drop_constraint('uq_dossier_cabinet_reference', 'dossiers', type_='unique')
    op.drop_index('ix_dossiers_reference', table_name='dossiers')
    op.create_index('ix_dossiers_reference', 'dossiers', ['reference'], unique=True)
    op.drop_constraint('fk_dossiers_cabinet', 'dossiers', type_='foreignkey')
    op.drop_column('dossiers', 'cabinet_id')
    
    # Restore unique constraints on clients
    op.drop_constraint('uq_client_cabinet_numero', 'clients', type_='unique')
    op.drop_index('ix_clients_numero_client', table_name='clients')
    op.create_index('ix_clients_numero_client', 'clients', ['numero_client'], unique=True)
    op.drop_constraint('fk_clients_cabinet', 'clients', type_='foreignkey')
    op.drop_column('clients', 'cabinet_id')
    
    # Restore unique constraints on users
    op.drop_constraint('uq_user_cabinet_username', 'users', type_='unique')
    op.drop_index('ix_users_username', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.drop_constraint('fk_users_cabinet', 'users', type_='foreignkey')
    op.drop_column('users', 'cabinet_id')
    
    # Drop cabinets table
    op.drop_index('ix_cabinets_slug', table_name='cabinets')
    op.drop_index('ix_cabinets_id', table_name='cabinets')
    op.drop_table('cabinets')