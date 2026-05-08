"""align legacy schema: nullable embedding_json + missing bill indexes

Revision ID: 4ceaeee93438
Revises: 52b5d3047141
Create Date: 2026-05-07 07:59:04.207034

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4ceaeee93438'
down_revision: Union[str, Sequence[str], None] = '52b5d3047141'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("bill_embeddings") as batch:
        batch.alter_column("embedding_json", existing_type=sa.Text(), nullable=True)
    op.create_index("ix_bills_agenda_date", "bills", ["agenda_date"])
    op.create_index("ix_bills_jurisdiction_level", "bills", ["jurisdiction_level"])


def downgrade() -> None:
    op.drop_index("ix_bills_jurisdiction_level", table_name="bills")
    op.drop_index("ix_bills_agenda_date", table_name="bills")
    with op.batch_alter_table("bill_embeddings") as batch:
        batch.alter_column("embedding_json", existing_type=sa.Text(), nullable=False)
