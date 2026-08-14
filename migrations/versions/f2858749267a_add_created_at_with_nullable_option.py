"""Add created_at with nullable option

Revision ID: f2858749267a
Revises: 8e112edd4c47
Create Date: 2026-08-14

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f2858749267a'
down_revision = '8e112edd4c47'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Vorab Enums bei Kunden & Lokal auf UPPERCASE korrigieren, damit SQLite-Alter nicht crasht
    op.execute("UPDATE agents SET memory_mode = UPPER(memory_mode) WHERE memory_mode IS NOT NULL;")
    op.execute("UPDATE agents SET memory_limit_type = UPPER(memory_limit_type) WHERE memory_limit_type IS NOT NULL;")

    # 2. 'agents' anpassen
    with op.batch_alter_table('agents', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP'))
        )
        batch_op.alter_column('system_prompt', existing_type=sa.TEXT(), nullable=True)
        batch_op.alter_column('memory_mode',
               existing_type=sa.VARCHAR(length=50),
               type_=sa.Enum('USER_ONLY', 'ALL', name='memorymode'),
               existing_nullable=False,
               existing_server_default=sa.text("'user_only'"))
        batch_op.alter_column('memory_limit_type',
               existing_type=sa.VARCHAR(length=50),
               type_=sa.Enum('ALL', 'MESSAGE_COUNT', name='memorylimittype'),
               existing_nullable=False,
               existing_server_default=sa.text("'all'"))

    # 3. 'datasources' anpassen (server_default verhindert NOT NULL crash bei vorhandenen Daten)
    with op.batch_alter_table('datasources', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP'))
        )
        batch_op.alter_column('agent_id', existing_type=sa.VARCHAR(length=36), nullable=True)

    # 4. 'message_attachments' anpassen
    with op.batch_alter_table('message_attachments', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP'))
        )

    # 5. 'llm_executions' Enum-Anpassung
    with op.batch_alter_table('llm_executions', schema=None) as batch_op:
        batch_op.alter_column('response_type',
               existing_type=sa.VARCHAR(length=50),
               type_=sa.Enum('SIMPLE_MESSAGE', 'TASK_CHAIN', name='responsetype'),
               existing_nullable=False)


def downgrade():
    with op.batch_alter_table('message_attachments', schema=None) as batch_op:
        batch_op.drop_column('created_at')

    with op.batch_alter_table('datasources', schema=None) as batch_op:
        batch_op.drop_column('created_at')

    with op.batch_alter_table('agents', schema=None) as batch_op:
        batch_op.drop_column('created_at')
