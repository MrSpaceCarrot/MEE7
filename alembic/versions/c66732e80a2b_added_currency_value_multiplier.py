"""Added currency value multiplier

Revision ID: c66732e80a2b
Revises: 1075b7c4ab97
Create Date: 2025-04-30 19:35:42.366141

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c66732e80a2b'
down_revision: Union[str, None] = '1075b7c4ab97'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
