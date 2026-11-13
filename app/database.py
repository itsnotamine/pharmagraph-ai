import json
import os
import sqlite3
import uuid

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path(
    os.getenv("DATABASE_PATH", "/app/data/pharmagraph.db")
)


def now():
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def db_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.row_factory = sqlite3.Row

    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_database():
    with db_connection() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_email TEXT NOT NULL,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                FOREIGN KEY (conversation_id)
                    REFERENCES conversations(id)
                    ON DELETE CASCADE
            )
        """)

        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversations_user
            ON conversations(user_email, updated_at)
        """)


def create_conversation(user_email, title="New conversation"):
    conversation_id = str(uuid.uuid4())
    timestamp = now()

    with db_connection() as db:
        db.execute(
            """
            INSERT INTO conversations
            (id, user_email, title, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                conversation_id,
                user_email,
                title,
                timestamp,
                timestamp,
            ),
        )

    return conversation_id


def list_conversations(user_email):
    with db_connection() as db:
        rows = db.execute(
            """
            SELECT id, title, created_at, updated_at
            FROM conversations
            WHERE user_email = ?
            ORDER BY updated_at DESC
            """,
            (user_email,),
        ).fetchall()

    return [dict(row) for row in rows]


def get_conversation(user_email, conversation_id):
    with db_connection() as db:
        conversation = db.execute(
            """
            SELECT *
            FROM conversations
            WHERE id = ? AND user_email = ?
            """,
            (conversation_id, user_email),
        ).fetchone()

        if not conversation:
            return None

        messages = db.execute(
            """
            SELECT id, role, content, metadata, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY created_at, rowid
            """,
            (conversation_id,),
        ).fetchall()

    result = dict(conversation)
    result["messages"] = [
        {
            **dict(message),
            "metadata": json.loads(message["metadata"]),
        }
        for message in messages
    ]

    return result


def add_message(
    user_email,
    conversation_id,
    role,
    content,
    metadata=None,
):
    message_id = str(uuid.uuid4())
    timestamp = now()

    with db_connection() as db:
        conversation = db.execute(
            """
            SELECT id, title
            FROM conversations
            WHERE id = ? AND user_email = ?
            """,
            (conversation_id, user_email),
        ).fetchone()

        if not conversation:
            return False

        db.execute(
            """
            INSERT INTO messages
            (id, conversation_id, role, content, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                message_id,
                conversation_id,
                role,
                content,
                json.dumps(metadata or {}),
                timestamp,
            ),
        )

        if role == "user" and conversation["title"] == "New conversation":
            title = content[:70]

            db.execute(
                """
                UPDATE conversations
                SET title = ?, updated_at = ?
                WHERE id = ?
                """,
                (title, timestamp, conversation_id),
            )
        else:
            db.execute(
                """
                UPDATE conversations
                SET updated_at = ?
                WHERE id = ?
                """,
                (timestamp, conversation_id),
            )

    return True


def delete_conversation(user_email, conversation_id):
    with db_connection() as db:
        db.execute("PRAGMA foreign_keys = ON")

        cursor = db.execute(
            """
            DELETE FROM conversations
            WHERE id = ? AND user_email = ?
            """,
            (conversation_id, user_email),
        )

        return cursor.rowcount > 0
