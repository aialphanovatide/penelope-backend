"""Add thread relationship to File models

Revision ID: 863a9005e753
Revises: b57f99881983
Create Date: 2024-09-06 13:44:42.418833

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '863a9005e753'
down_revision: Union[str, None] = 'b57f99881983'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('files', sa.Column('user_id', sa.String(length=255), nullable=False))
    op.add_column('files', sa.Column('thread_id', sa.String(length=32), nullable=True))
    op.create_foreign_key(None, 'files', 'threads', ['thread_id'], ['id'])
    op.create_foreign_key(None, 'files', 'users', ['user_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'files', type_='foreignkey')
    op.drop_constraint(None, 'files', type_='foreignkey')
    op.drop_column('files', 'thread_id')
    op.drop_column('files', 'user_id')
    # ### end Alembic commands ###