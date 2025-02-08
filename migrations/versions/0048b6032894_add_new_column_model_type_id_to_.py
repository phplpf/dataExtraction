"""add new column model_type_id  to existing table modelservice 

Revision ID: 0048b6032894
Revises: 
Create Date: 2025-01-03 19:34:03.173213

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0048b6032894'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('modelservice', sa.Column('model_type_id', sa.Integer(), nullable=True, comment='模型类型id'))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('modelservice', 'model_type_id')
    # ### end Alembic commands ###
