"""initial: manifestations e attachments (MySQL)

Revision ID: 001
Revises:
Create Date: 2026-01-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # MySQL: ENUMs como tipos nativos
    channel_enum = sa.Enum(
        "text", "audio", "image", "video", "mixed",
        name="channel_enum",
        create_constraint=True,
    )
    status_enum = sa.Enum(
        "received", "processing", "completed",
        name="status_enum",
        create_constraint=True,
    )
    attachment_type_enum = sa.Enum(
        "audio", "image", "video",
        name="attachment_type_enum",
        create_constraint=True,
    )

    op.create_table(
        "manifestations",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("protocol", sa.String(32), nullable=False),
        sa.Column("channel", channel_enum, nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("anonymous", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", status_enum, nullable=False, server_default="received"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("ix_manifestations_protocol", "manifestations", ["protocol"], unique=True)

    op.create_table(
        "attachments",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("manifestation_id", sa.String(36), nullable=False),
        sa.Column("type", attachment_type_enum, nullable=False),
        sa.Column("mime_type", sa.String(128), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("file_path", sa.String(512), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["manifestation_id"], ["manifestations.id"], ondelete="CASCADE"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("ix_attachments_manifestation_id", "attachments", ["manifestation_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_attachments_manifestation_id", table_name="attachments")
    op.drop_table("attachments")
    op.drop_index("ix_manifestations_protocol", table_name="manifestations")
    op.drop_table("manifestations")
    # MySQL: ENUM é tipo da coluna, não objeto separado; drop das tabelas basta.
