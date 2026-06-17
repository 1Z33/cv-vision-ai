"""add analysis used_gemini column

Revision ID: 9dc2ae5a3b8f
Revises: 1cc75f0afe76
Create Date: 2026-06-06 23:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9dc2ae5a3b8f'
down_revision = '1cc75f0afe76'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'analyses',
        sa.Column('used_gemini', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column('analyses', 'used_gemini', server_default=None)


def downgrade() -> None:
    op.drop_column('analyses', 'used_gemini')
