"""
SQLite Schema and Migration Definitions for VidyaVerse.
Enforces durable persistence of conversations, messages, learning progress, and quiz attempts.
"""
from __future__ import annotations

import sqlite3

DDL_CONVERSATIONS = """
CREATE TABLE IF NOT EXISTS conversations (
    conversation_id TEXT PRIMARY KEY,
    subject_id TEXT NOT NULL,
    chapter_id TEXT,
    chat_scope TEXT NOT NULL CHECK(chat_scope IN ('subject', 'chapter')),
    persona_id TEXT NOT NULL,
    title TEXT NOT NULL,
    learning_state TEXT NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
"""

DDL_MESSAGES = """
CREATE TABLE IF NOT EXISTS messages (
    message_id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    response_format TEXT DEFAULT 'plain_text',
    response_mode TEXT DEFAULT 'textbook_grounded',
    citations TEXT DEFAULT '[]',
    suggested_actions TEXT DEFAULT '[]',
    created_at TIMESTAMP NOT NULL,
    metadata TEXT DEFAULT '{}'
);
"""

DDL_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_conv_subject_scope ON conversations(subject_id, chat_scope, updated_at DESC);",
    "CREATE INDEX IF NOT EXISTS idx_conv_chapter ON conversations(chapter_id, updated_at DESC);",
    "CREATE INDEX IF NOT EXISTS idx_conv_updated ON conversations(updated_at DESC);",
    "CREATE INDEX IF NOT EXISTS idx_msg_conv ON messages(conversation_id, created_at ASC);",
]


def init_schema(conn: sqlite3.Connection) -> None:
    """Create all required tables and indexes if they do not already exist."""
    with conn:
        conn.execute(DDL_CONVERSATIONS)
        conn.execute(DDL_MESSAGES)
        for idx in DDL_INDEXES:
            conn.execute(idx)
