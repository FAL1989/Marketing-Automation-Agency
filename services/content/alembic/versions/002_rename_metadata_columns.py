"""rename metadata columns

Revision ID: 002
Revises: 001
Create Date: 2024-01-10 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Renomear a coluna metadata para content_metadata na tabela contents
    op.alter_column('contents', 'metadata', new_column_name='content_metadata')
    
    # Renomear a coluna metadata para template_metadata na tabela templates
    op.alter_column('templates', 'metadata', new_column_name='template_metadata')

def downgrade() -> None:
    # Reverter a renomeação na tabela contents
    op.alter_column('contents', 'content_metadata', new_column_name='metadata')
    
    # Reverter a renomeação na tabela templates
    op.alter_column('templates', 'template_metadata', new_column_name='metadata') 