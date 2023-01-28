"""empty message

Revision ID: 5fcd7b61bbb4
Revises: 493f31c7ea08
Create Date: 2023-01-15 23:58:13.930875

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5fcd7b61bbb4'
down_revision = '493f31c7ea08'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user_libraries',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('systemid', sa.String(), nullable=True),
    sa.Column('systemname', sa.String(), nullable=True),
    sa.Column('libkey', sa.String(), nullable=True),
    sa.Column('libid', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user_libraries')
    # ### end Alembic commands ###
