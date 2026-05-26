"""Initial schema — users, conversations, messages, documents

Revision ID: 0001
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id",              sa.String(),  primary_key=True),
        sa.Column("email",           sa.String(255), nullable=False, unique=True),
        sa.Column("username",        sa.String(100), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("created_at",      sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active",       sa.Boolean(), nullable=False, server_default="true"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "conversations",
        sa.Column("id",         sa.String(), primary_key=True),
        sa.Column("user_id",    sa.String(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title",      sa.String(200), nullable=False, server_default="New conversation"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_conversations_user_id", "conversations", ["user_id"])

    op.create_table(
        "messages",
        sa.Column("id",              sa.String(), primary_key=True),
        sa.Column("conversation_id", sa.String(), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role",            sa.String(20), nullable=False),
        sa.Column("content",         sa.Text(), nullable=False),
        sa.Column("created_at",      sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])

    op.create_table(
        "documents",
        sa.Column("id",              sa.String(), primary_key=True),
        sa.Column("conversation_id", sa.String(), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename",        sa.String(255), nullable=False),
        sa.Column("chunks_created",  sa.Integer(), nullable=False, server_default="0"),
        sa.Column("uploaded_at",     sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_documents_conversation_id", "documents", ["conversation_id"])


def downgrade() -> None:
    op.drop_table("documents")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("users")
