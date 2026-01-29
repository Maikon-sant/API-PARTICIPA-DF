"""modernize manifestation flow: input_type, draft, local, contato, tags

Revision ID: 002
Revises: 001
Create Date: 2026-01-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.mysql import JSON

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    input_type_enum = sa.Enum(
        "text", "audio", "image", "video", "mixed",
        name="input_type_enum",
        create_constraint=True,
    )

    op.add_column("manifestations", sa.Column("input_type", input_type_enum, nullable=True))
    op.add_column("manifestations", sa.Column("original_text", sa.Text(), nullable=True))
    op.add_column("manifestations", sa.Column("extracted_text", sa.Text(), nullable=True))
    op.add_column("manifestations", sa.Column("subject_id", sa.String(64), nullable=True))
    op.add_column("manifestations", sa.Column("subject_label", sa.String(256), nullable=True))
    op.add_column("manifestations", sa.Column("complementary_tags", JSON, nullable=True))
    op.add_column("manifestations", sa.Column("summary", sa.Text(), nullable=True))
    op.add_column("manifestations", sa.Column("location_lat", sa.Float(), nullable=True))
    op.add_column("manifestations", sa.Column("location_lng", sa.Float(), nullable=True))
    op.add_column("manifestations", sa.Column("location_description", sa.String(512), nullable=True))
    op.add_column("manifestations", sa.Column("administrative_region", sa.String(128), nullable=True))
    op.add_column("manifestations", sa.Column("contact_name", sa.String(256), nullable=True))
    op.add_column("manifestations", sa.Column("contact_email", sa.String(256), nullable=True))
    op.add_column("manifestations", sa.Column("contact_phone", sa.String(32), nullable=True))

    op.execute("UPDATE manifestations SET input_type = channel, original_text = text")

    op.alter_column(
        "manifestations",
        "input_type",
        existing_type=input_type_enum,
        nullable=False,
    )
    op.drop_column("manifestations", "channel")
    op.drop_column("manifestations", "text")

    op.alter_column(
        "manifestations",
        "protocol",
        existing_type=sa.String(32),
        nullable=True,
    )

    op.execute(
        "ALTER TABLE manifestations MODIFY COLUMN status "
        "ENUM('draft','received','processing','completed') NOT NULL DEFAULT 'draft'"
    )


def downgrade() -> None:
    op.execute("UPDATE manifestations SET status = 'received' WHERE status = 'draft'")
    op.execute(
        "ALTER TABLE manifestations MODIFY COLUMN status "
        "ENUM('received','processing','completed') NOT NULL DEFAULT 'received'"
    )
    op.alter_column(
        "manifestations",
        "protocol",
        existing_type=sa.String(32),
        nullable=False,
    )

    channel_enum = sa.Enum(
        "text", "audio", "image", "video", "mixed",
        name="channel_enum",
        create_constraint=True,
    )
    op.add_column("manifestations", sa.Column("channel", channel_enum, nullable=True))
    op.add_column("manifestations", sa.Column("text", sa.Text(), nullable=True))
    op.execute("UPDATE manifestations SET channel = input_type, text = original_text")
    op.alter_column("manifestations", "channel", nullable=False)

    op.drop_column("manifestations", "input_type")
    op.drop_column("manifestations", "original_text")
    op.drop_column("manifestations", "extracted_text")
    op.drop_column("manifestations", "subject_id")
    op.drop_column("manifestations", "subject_label")
    op.drop_column("manifestations", "complementary_tags")
    op.drop_column("manifestations", "summary")
    op.drop_column("manifestations", "location_lat")
    op.drop_column("manifestations", "location_lng")
    op.drop_column("manifestations", "location_description")
    op.drop_column("manifestations", "administrative_region")
    op.drop_column("manifestations", "contact_name")
    op.drop_column("manifestations", "contact_email")
    op.drop_column("manifestations", "contact_phone")
