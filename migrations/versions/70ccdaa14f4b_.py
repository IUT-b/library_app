"""empty message

Revision ID: 70ccdaa14f4b
Revises: 8dc489aa6e97
Create Date: 2023-01-14 05:51:28.944831

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '70ccdaa14f4b'
down_revision = '8dc489aa6e97'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user_books',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('book', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('user_image_tags')
    op.drop_table('user_images')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user_images',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('user_id', sa.VARCHAR(), nullable=True),
    sa.Column('image_path', sa.VARCHAR(), nullable=True),
    sa.Column('is_detected', sa.BOOLEAN(), nullable=True),
    sa.Column('created_at', sa.DATETIME(), nullable=True),
    sa.Column('updated_at', sa.DATETIME(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user_image_tags',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('user_image_id', sa.VARCHAR(), nullable=True),
    sa.Column('tag_name', sa.VARCHAR(), nullable=True),
    sa.Column('created_at', sa.DATETIME(), nullable=True),
    sa.Column('updated_at', sa.DATETIME(), nullable=True),
    sa.ForeignKeyConstraint(['user_image_id'], ['user_images.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('user_books')
    # ### end Alembic commands ###
