"""Add login attempt tracking and suspension fields to users

Revision ID: 7cab9fb096ed
Revises: b90f227d6985
Create Date: 2025-08-18 08:55:15.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '7cab9fb096ed'
down_revision: Union[str, Sequence[str], None] = 'b90f227d6985'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('is_suspended', sa.Boolean(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('users', 'is_suspended')
    op.drop_column('users', 'failed_login_attempts')
