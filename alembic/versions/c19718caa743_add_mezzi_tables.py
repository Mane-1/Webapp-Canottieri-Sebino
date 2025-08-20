"""add_mezzi_tables

Revision ID: c19718caa743
Revises: 7cab9fb096ed
Create Date: 2025-08-20 14:37:45.830502

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c19718caa743'
down_revision: Union[str, Sequence[str], None] = '7cab9fb096ed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Creazione tabella furgoni
    op.create_table('furgoni',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('marca', sa.String(), nullable=False),
        sa.Column('modello', sa.String(), nullable=False),
        sa.Column('targa', sa.String(), nullable=False),
        sa.Column('anno', sa.Integer(), nullable=False),
        sa.Column('stato', sa.Enum('libero', 'manutenzione', 'fuori_uso', 'trasferta', name='stato_furgone'), nullable=False),
        sa.Column('scadenza_bollo', sa.Date(), nullable=True),
        sa.Column('scadenza_revisione', sa.Date(), nullable=True),
        sa.Column('scadenza_rca', sa.Date(), nullable=True),
        sa.Column('scadenza_infortuni_conducente', sa.Date(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_furgoni_id'), 'furgoni', ['id'], unique=False)
    op.create_index(op.f('ix_furgoni_targa'), 'furgoni', ['targa'], unique=True)
    
    # Creazione tabella gommoni
    op.create_table('gommoni',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(), nullable=False),
        sa.Column('motore', sa.String(), nullable=True),
        sa.Column('potenza', sa.String(), nullable=True),
        sa.Column('stato', sa.Enum('libero', 'manutenzione', 'fuori_uso', name='stato_gommone'), nullable=False),
        sa.Column('scadenza_rca', sa.Date(), nullable=True),
        sa.Column('scadenza_manutenzione', sa.Date(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_gommoni_id'), 'gommoni', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Rimozione tabella gommoni
    op.drop_index(op.f('ix_gommoni_id'), table_name='gommoni')
    op.drop_table('gommoni')
    
    # Rimozione tabella furgoni
    op.drop_index(op.f('ix_furgoni_targa'), table_name='furgoni')
    op.drop_index(op.f('ix_furgoni_id'), table_name='furgoni')
    op.drop_table('furgoni')
    
    # Rimozione enum types
    op.execute("DROP TYPE IF EXISTS stato_gommone")
    op.execute("DROP TYPE IF EXISTS stato_furgone")
