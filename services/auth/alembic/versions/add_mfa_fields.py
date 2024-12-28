"""add mfa fields

Revision ID: add_mfa_fields
Revises: 
Create Date: 2024-03-13 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_mfa_fields'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade():
    # Adiciona campos MFA à tabela users
    op.add_column('users', sa.Column('mfa_enabled', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('users', sa.Column('mfa_secret', sa.String(), nullable=True))
    op.add_column('users', sa.Column('last_login', sa.DateTime(timezone=True), nullable=True))

def downgrade():
    # Remove campos MFA da tabela users
    op.drop_column('users', 'mfa_enabled')
    op.drop_column('users', 'mfa_secret')
    op.drop_column('users', 'last_login') 