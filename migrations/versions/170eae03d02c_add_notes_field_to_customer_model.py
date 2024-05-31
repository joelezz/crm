"""Add notes field to Customer model

Revision ID: 170eae03d02c
Revises: 
Create Date: 2023-05-30 12:34:56.789123

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '170eae03d02c'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('customer') as batch_op:
        batch_op.add_column(sa.Column('notes', sa.String(length=50), nullable=False, server_default=''))
    with op.batch_alter_table('customer') as batch_op:
        batch_op.alter_column('notes', server_default=None)

def downgrade():
    with op.batch_alter_table('customer') as batch_op:
        batch_op.drop_column('notes')
