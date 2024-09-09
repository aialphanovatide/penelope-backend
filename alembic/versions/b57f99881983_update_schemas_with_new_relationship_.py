"""Update schemas with new relationship between file and thread schema

Revision ID: b57f99881983
Revises: 70f145538619
Create Date: 2024-09-06 13:42:02.255750

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b57f99881983'
down_revision: Union[str, None] = '70f145538619'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
