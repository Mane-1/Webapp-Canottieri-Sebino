"""Merge heads

Revision ID: 9755c9ebfca5
Revises: add_equipaggi_table, add_scadenze_fields
Create Date: 2025-09-14 17:15:33.371440

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9755c9ebfca5'
down_revision: Union[str, Sequence[str], None] = ('add_equipaggi_table', 'add_scadenze_fields')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
