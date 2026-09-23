"""Add version and environment to metrics

Revision ID: a9f3b2e4d501
Revises: c13242147023
Create Date: 2026-09-23 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a9f3b2e4d501'
down_revision: Union[str, Sequence[str], None] = 'c13242147023'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add version and environment columns to metrics table."""
    op.add_column('metrics', sa.Column('version', sa.String(), nullable=True))
    op.add_column('metrics', sa.Column('environment', sa.String(), nullable=True))


def downgrade() -> None:
    """Remove version and environment columns from metrics table."""
    op.drop_column('metrics', 'environment')
    op.drop_column('metrics', 'version')
