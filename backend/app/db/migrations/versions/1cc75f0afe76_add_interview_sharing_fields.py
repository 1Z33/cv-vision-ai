"""add interview sharing fields

Revision ID: 1cc75f0afe76
Revises: 55007501b0f4
Create Date: 2026-06-01 20:09:55.286996

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1cc75f0afe76'
down_revision = '55007501b0f4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ajouter les colonnes à interview_sessions
    op.add_column(
        'interview_sessions',
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default=sa.text('false')),
    )
    op.add_column(
        'interview_sessions',
        sa.Column('share_token', sa.String(length=64), nullable=True),
    )
    op.add_column(
        'interview_sessions',
        sa.Column('shared_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Index unique sur share_token
    op.create_index(
        'ix_interview_sessions_share_token',
        'interview_sessions',
        ['share_token'],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index('ix_interview_sessions_share_token', table_name='interview_sessions')
    op.drop_column('interview_sessions', 'shared_at')
    op.drop_column('interview_sessions', 'share_token')
    op.drop_column('interview_sessions', 'is_public')


