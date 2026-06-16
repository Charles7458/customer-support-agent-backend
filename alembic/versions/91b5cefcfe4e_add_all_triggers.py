"""add_all_triggers

Revision ID: 91b5cefcfe4e
Revises: c0596f16a69a
Create Date: 2026-06-16 08:22:46.431721

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '91b5cefcfe4e'
down_revision: Union[str, Sequence[str], None] = 'c0596f16a69a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # 1. Update parent conversation trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION update_parent_conversation()
        RETURNS TRIGGER AS $$
        BEGIN
            UPDATE conversations
            SET updated_at = CURRENT_TIMESTAMP,
            last_message_id = NEW.id
            WHERE id = NEW.conversation_id;
            RETURN NEW;
        END; 
        $$ LANGUAGE plpgsql;
    """)
    
    op.execute("""
        CREATE TRIGGER trg_update_parent_conversation
        AFTER INSERT ON messages
        FOR EACH ROW
        EXECUTE FUNCTION update_parent_conversation();
    """)
    
    # 2. Update parent ticket trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION update_parent_ticket()
        RETURNS TRIGGER AS $$
        BEGIN
            UPDATE tickets
            SET updated_at = CURRENT_TIMESTAMP
            WHERE conversation_id = NEW.id;
            RETURN NEW;
        END; 
        $$ LANGUAGE plpgsql;
    """)
    
    op.execute("""
        CREATE TRIGGER trg_update_parent_ticket
        AFTER UPDATE ON conversations
        FOR EACH ROW
        EXECUTE FUNCTION update_parent_ticket();
    """)

    # 3. Update ticket updated_at timestamp trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION update_ticket_timestamp()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END; 
        $$ LANGUAGE plpgsql;
    """)
    
    op.execute("""
        CREATE TRIGGER trg_update_ticket_updated_at
        BEFORE UPDATE ON tickets
        FOR EACH ROW
        EXECUTE FUNCTION update_ticket_timestamp();
    """)

    # 4. Update user updated_at trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION update_user_timestamp()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END; 
        $$ LANGUAGE plpgsql;
    """)
    
    op.execute("""
        CREATE TRIGGER trg_update_user_updated_at
        BEFORE UPDATE ON users
        FOR EACH ROW
        EXECUTE FUNCTION update_user_timestamp();
    """)


    # 5. Update parent order updated_at timestamp trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION update_parent_order_timestamp()
        RETURNS TRIGGER AS $$
        BEGIN
            UPDATE orders
            SET last_update = CURRENT_TIMESTAMP
            WHERE id = NEW.order_id;
            RETURN NEW;
        END; 
        $$ LANGUAGE plpgsql;
    """)
    
    op.execute("""
        CREATE TRIGGER trg_update_parent_order
        AFTER INSERT ON tracking
        FOR EACH ROW
        EXECUTE FUNCTION update_parent_order_timestamp();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Always provide a way to remove it if you roll back
    op.execute("DROP TRIGGER IF EXISTS trg_update_parent_conversation ON messages;")
    op.execute("DROP FUNCTION IF EXISTS update_parent_conversation();")

    op.execute("DROP TRIGGER IF EXISTS trg_update_parent_ticket ON conversations;")
    op.execute("DROP FUNCTION IF EXISTS update_parent_ticket();")

    op.execute("DROP TRIGGER IF EXISTS trg_update_ticket_updated_at ON tickets;")
    op.execute("DROP FUNCTION IF EXISTS update_ticket_timestamp();")

    op.execute("DROP TRIGGER IF EXISTS trg_update_user_updated_at ON users;")
    op.execute("DROP FUNCTION IF EXISTS update_user_timestamp();")

    op.execute("DROP TRIGGER IF EXISTS trg_update_parent_order ON tracking;")
    op.execute("DROP FUNCTION IF EXISTS update_parent_order_timestamp();")
