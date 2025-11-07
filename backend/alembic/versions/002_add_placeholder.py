"""Placeholder migration for missing revision 002

Revision ID: 002
Revises: 001
Create Date: 2025-11-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No-op placeholder migration created to satisfy missing revision 002."""
    pass


def downgrade() -> None:
    """No-op downgrade for placeholder migration."""
    pass
