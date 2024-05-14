"""user and role table

Revision ID: 86085e44f737
Revises: 
Create Date: 2024-03-29 23:04:38.146760

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '86085e44f737'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('role',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=80), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=64), nullable=False),
    sa.Column('password_hash', sa.String(length=256), nullable=True),
    sa.Column('weekly_limit', sa.Integer(), nullable=True),
    sa.Column('balance', sa.Integer(), nullable=True),
    sa.Column('pages_printed', sa.Integer(), nullable=True),
    sa.Column('weekly_print_number', sa.Integer(), nullable=True),
    sa.Column('room_number', sa.Integer(), nullable=False),
    sa.Column('role_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['role_id'], ['role.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_user_username'), ['username'], unique=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_user_username'))

    op.drop_table('user')
    op.drop_table('role')
    # ### end Alembic commands ###
