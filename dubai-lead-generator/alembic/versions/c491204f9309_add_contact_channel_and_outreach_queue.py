"""add_contact_channel_and_outreach_queue

Revision ID: c491204f9309
Revises: b312604f9308
Create Date: 2026-09-24 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c491204f9309'
down_revision: Union[str, Sequence[str], None] = 'b312604f9308'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('businesses', schema=None) as batch_op:
        batch_op.add_column(sa.Column('contact_channel', sa.String(), nullable=True, server_default='email'))

    op.create_table(
        'outreach_queue',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('business_id', sa.String(), nullable=False),
        sa.Column('channel', sa.String(), nullable=True, server_default='email'),
        sa.Column('recipient', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True, server_default='PENDING'),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('follow_up_date', sa.DateTime(), nullable=True),
        sa.Column('sequence_step', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_outreach_queue_business_id'), 'outreach_queue', ['business_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_outreach_queue_business_id'), table_name='outreach_queue')
    op.drop_table('outreach_queue')
    with op.batch_alter_table('businesses', schema=None) as batch_op:
        batch_op.drop_column('contact_channel')
