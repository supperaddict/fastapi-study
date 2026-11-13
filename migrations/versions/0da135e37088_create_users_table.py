"""create users table

Revision ID: 0da135e37088
Revises: 
Create Date: 2026-11-12 12:35:20.258162

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0da135e37088'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column(
            "id",
            sa.Integer(),
            sa.Identity(always=True),
            nullable=False,
        ),
        sa.Column(
            "username",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "age",
            sa.Integer(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
        sa.CheckConstraint(
            "age BETWEEN 0 AND 150",
            name="users_age_check",
        ),
    )


def downgrade() -> None:
    op.drop_table("users")