"""Add memory settings to agents table

Revision ID: 8e112edd4c47
Revises: faacee40e77b
Create Date: 2026-08-13 15:36:21.722019

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8e112edd4c47'
down_revision = 'faacee40e77b'
branch_labels = None
depends_on = None


def upgrade():
    # Wir setzen server_default, damit bestehende Datensätze einen Wert bekommen
    op.add_column(
        'agents', 
        sa.Column('memory_enabled', sa.Boolean(), nullable=False, server_default=sa.text('0'))
    )
    op.add_column(
        'agents', 
        sa.Column('memory_mode', sa.String(length=50), nullable=False, server_default='user_only')
    )
    op.add_column(
        'agents', 
        sa.Column('memory_limit_type', sa.String(length=50), nullable=False, server_default='all')
    )
    op.add_column(
        'agents', 
        sa.Column('memory_message_count', sa.Integer(), nullable=True)
    )


def downgrade():
    # Falls SQLite 'batch_alter_table' benötigt (je nach Alembic-Konfiguration für SQLite Drops):
    with op.batch_alter_table('agents', schema=None) as batch_op:
        batch_op.drop_column('memory_message_count')
        batch_op.drop_column('memory_limit_type')
        batch_op.drop_column('memory_mode')
        batch_op.drop_column('memory_enabled')

