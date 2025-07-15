"""add_documents_requis_table

Revision ID: a7b0f77399b0
Revises: f3ad6a9dde9d
Create Date: 2025-07-12 12:58:00.036419

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a7b0f77399b0'
down_revision: Union[str, Sequence[str], None] = 'f3ad6a9dde9d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Créer la table documents_requis
    op.create_table('documents_requis',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dossier_id', sa.Integer(), nullable=False),
        sa.Column('echeance_id', sa.Integer(), nullable=False),
        sa.Column('type_document', postgresql.ENUM(
            'FACTURE_ACHAT', 'RELEVE_BANCAIRE', 'FACTURE_VENTE', 
            'ETAT_PAIE', 'DECLARATION_IMPOT', 'DECLARATION_TVA',
            'DECLARATION_SOCIALE', 'CONTRAT', 'COURRIER', 'AUTRE',
            name='typedocument', create_type=False
        ), nullable=False),
        sa.Column('mois', sa.Integer(), nullable=False),
        sa.Column('annee', sa.Integer(), nullable=False),
        sa.Column('est_applicable', sa.Boolean(), nullable=True, default=True),
        sa.Column('est_fourni', sa.Boolean(), nullable=True, default=False),
        sa.ForeignKeyConstraint(['dossier_id'], ['dossiers.id'], ),
        sa.ForeignKeyConstraint(['echeance_id'], ['echeances.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_documents_requis_id'), 'documents_requis', ['id'], unique=False)
    op.create_index(op.f('ix_documents_requis_dossier_id'), 'documents_requis', ['dossier_id'], unique=False)
    op.create_index(op.f('ix_documents_requis_echeance_id'), 'documents_requis', ['echeance_id'], unique=False)
    
    # Créer des documents requis pour les échéances existantes
    connection = op.get_bind()
    
    # Types de documents standards par service
    documents_par_service = {
        'COMPTABILITE': ['RELEVE_BANCAIRE', 'FACTURE_ACHAT', 'FACTURE_VENTE'],
        'FISCALITE': ['DECLARATION_TVA', 'DECLARATION_IMPOT'],
        'PAIE': ['ETAT_PAIE', 'DECLARATION_SOCIALE'],
        'JURIDIQUE': ['CONTRAT', 'COURRIER'],
        'AUDIT': ['RELEVE_BANCAIRE', 'FACTURE_ACHAT', 'FACTURE_VENTE'],
        'CONSEIL': ['CONTRAT', 'COURRIER'],
        'AUTRE': ['AUTRE']
    }
    
    # Récupérer toutes les échéances avec leur dossier
    result = connection.execute(sa.text("""
        SELECT e.id as echeance_id, e.mois, e.annee, e.dossier_id, d.type_dossier
        FROM echeances e
        JOIN dossiers d ON e.dossier_id = d.id
    """))
    
    for row in result:
        type_dossier = row.type_dossier
        docs_requis = documents_par_service.get(type_dossier, ['AUTRE'])
        
        for type_doc in docs_requis:
            connection.execute(sa.text("""
                INSERT INTO documents_requis (dossier_id, echeance_id, type_document, mois, annee, est_applicable, est_fourni)
                VALUES (:dossier_id, :echeance_id, :type_document, :mois, :annee, true, false)
            """), {
                'dossier_id': row.dossier_id,
                'echeance_id': row.echeance_id,
                'type_document': type_doc,
                'mois': row.mois,
                'annee': row.annee
            })


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_documents_requis_echeance_id'), table_name='documents_requis')
    op.drop_index(op.f('ix_documents_requis_dossier_id'), table_name='documents_requis')
    op.drop_index(op.f('ix_documents_requis_id'), table_name='documents_requis')
    op.drop_table('documents_requis')
