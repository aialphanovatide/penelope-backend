"""Add thread relationship to File model

Revision ID: 70f145538619
Revises: 95f8dca52963
Create Date: 2024-09-06 13:36:08.531110

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '70f145538619'
down_revision: Union[str, None] = '95f8dca52963'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
