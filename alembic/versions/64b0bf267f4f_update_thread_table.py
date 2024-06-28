"""update thread table

Revision ID: 64b0bf267f4f
Revises: c008f28fbbad
Create Date: 2024-06-28 12:12:32.115453

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '64b0bf267f4f'
down_revision: Union[str, None] = 'c008f28fbbad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
