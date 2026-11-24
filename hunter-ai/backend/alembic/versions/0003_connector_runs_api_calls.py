"""compteur d'appels API par exécution de connecteur (quotas)

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-24 12:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "connector_runs",
        sa.Column("api_calls", sa.Integer(), server_default="0", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("connector_runs", "api_calls")
