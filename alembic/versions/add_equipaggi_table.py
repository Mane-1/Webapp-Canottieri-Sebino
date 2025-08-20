"""Add equipaggi table

Revision ID: add_equipaggi_table
Revises: c19718caa743
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = 'add_equipaggi_table'
down_revision = 'b90f227d6985'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create equipaggi table
    op.create_table('equipaggi',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=100), nullable=False),
        sa.Column('barca_id', sa.Integer(), nullable=False),
        sa.Column('capovoga_id', sa.Integer(), nullable=False),
        sa.Column('secondo_id', sa.Integer(), nullable=True),
        sa.Column('terzo_id', sa.Integer(), nullable=True),
        sa.Column('quarto_id', sa.Integer(), nullable=True),
        sa.Column('quinto_id', sa.Integer(), nullable=True),
        sa.Column('sesto_id', sa.Integer(), nullable=True),
        sa.Column('settimo_id', sa.Integer(), nullable=True),
        sa.Column('prodiere_id', sa.Integer(), nullable=True),
        sa.Column('timoniere_id', sa.Integer(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['barca_id'], ['barche.id'], ),
        sa.ForeignKeyConstraint(['capovoga_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['secondo_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['terzo_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['quarto_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['quinto_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['sesto_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['settimo_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['prodiere_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['timoniere_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index on barca_id for performance
    op.create_index(op.f('ix_equipaggi_barca_id'), 'equipaggi', ['barca_id'], unique=False)
    op.create_index(op.f('ix_equipaggi_id'), 'equipaggi', ['id'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_equipaggi_id'), table_name='equipaggi')
    op.drop_index(op.f('ix_equipaggi_barca_id'), table_name='equipaggi')
    
    # Drop table
    op.drop_table('equipaggi')
