"""add mfa backup fields

Revision ID: add_mfa_backup_fields
Revises: add_mfa_fields
Create Date: 2024-03-14 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_mfa_backup_fields'
down_revision = 'add_mfa_fields'
branch_labels = None
depends_on = None

def upgrade():
    # Adiciona campos de backup MFA à tabela users
    op.add_column('users', sa.Column('mfa_backup_codes', sa.JSON(), nullable=True))
    op.add_column('users', sa.Column('mfa_last_used', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('mfa_recovery_email', sa.String(), nullable=True))
    op.add_column('users', sa.Column('mfa_attempts', sa.Integer(), server_default='0', nullable=False))
    op.add_column('users', sa.Column('mfa_locked_until', sa.DateTime(timezone=True), nullable=True))

def downgrade():
    # Remove campos de backup MFA da tabela users
    op.drop_column('users', 'mfa_backup_codes')
    op.drop_column('users', 'mfa_last_used')
    op.drop_column('users', 'mfa_recovery_email')
    op.drop_column('users', 'mfa_attempts')
    op.drop_column('users', 'mfa_locked_until') 