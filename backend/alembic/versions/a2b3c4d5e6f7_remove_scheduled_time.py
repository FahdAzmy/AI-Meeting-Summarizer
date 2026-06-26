"""remove scheduled_time from meetings

Revision ID: a2b3c4d5e6f7
Revises: fe65a54c6ec6
Create Date: 2026-06-18 07:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a2b3c4d5e6f7"
down_revision: Union[str, Sequence[str], None] = "fe65a54c6ec6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("meetings", "scheduled_time")


def downgrade() -> None:
    op.add_column(
        "meetings",
        sa.Column("scheduled_time", sa.DateTime(timezone=True), nullable=True),
    )
