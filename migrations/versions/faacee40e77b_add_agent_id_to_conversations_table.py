"""add agent_id to conversations table

Revision ID: faacee40e77b
Revises: a2bc1276f9b4
Create Date: 2026-08-12 17:58:51.408454

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'faacee40e77b'
down_revision = 'a2bc1276f9b4'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Spalte agent_id als nullable hinzufügen
    with op.batch_alter_table('conversations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('agent_id', sa.String(length=36), nullable=True))

    # 2. Bestehende Daten migrieren: agent_id = id
    op.execute("UPDATE conversations SET agent_id = id WHERE agent_id IS NULL")

    # 3. Foreign Key Constraint nachträglich hinzufügen
    with op.batch_alter_table('conversations', schema=None) as batch_op:
        batch_op.create_foreign_key(
            'fk_conversations_agent_id', 
            'agents', 
            ['agent_id'], 
            ['id']
        )


def downgrade():
    with op.batch_alter_table('conversations', schema=None) as batch_op:
        batch_op.drop_constraint('fk_conversations_agent_id', type_='foreignkey')
        batch_op.drop_column('agent_id')