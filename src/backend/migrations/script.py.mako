"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision if down_revision else 'None'}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes

# revision identifiers, used by Alembic.
revision = "${up_revision}"
down_revision = ${repr(down_revision) if down_revision else "None"}
branch_labels = ${repr(branch_labels) if branch_labels else "None"}
depends_on = ${repr(depends_on) if depends_on else "None"}


def upgrade():
    """Apply migration changes.

    Add or modify database structures here.

    Example:
    op.add_column("users", sa.Column("new_column", sa.String(length=255), nullable=True))
    op.create_index("ix_users_new_column", "users", ["new_column"])
    """
    ${upgrades if upgrades else "pass"}


def downgrade():
    """Rollback migration changes.

    Undo changes made in upgrade().

    Example:
    op.drop_index("ix_users_new_column", table_name="users")
    op.drop_column("users", "new_column")
    """
    ${downgrades if downgrades else "pass"}
