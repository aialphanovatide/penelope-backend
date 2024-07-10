"""Update user table with picture column

Revision ID: 42c5b45076d5
Revises: dd7aa0b339f8
Create Date: 2024-07-07 19:14:57.772315

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '42c5b45076d5'
down_revision: Union[str, None] = 'dd7aa0b339f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('picture', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'picture')
    # ### end Alembic commands ###