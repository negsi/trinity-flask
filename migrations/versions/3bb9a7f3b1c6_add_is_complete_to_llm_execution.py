"""add_is_complete_to_llm_execution

Revision ID: 3bb9a7f3b1c6
Revises: 1ce3170726bf
Create Date: 2026-07-29 17:17:22.153587

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3bb9a7f3b1c6'
down_revision = '1ce3170726bf'
branch_labels = None
depends_on = None


def upgrade():
    # server_default sorgt dafür, dass bestehende Zeilen '1' (True) erhalten!
    op.add_column(
        'llm_executions',
        sa.Column('is_complete', sa.Boolean(), server_default=sa.text('1'), nullable=False)
    )


def downgrade():
    op.drop_column('llm_executions', 'is_complete')