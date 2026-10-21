"""
SQLite Repository for Conversations and Messages in VidyaVerse.
Guarantees durable persistence surviving server restarts, strict scope queries,
persona identity locking, and learning state tracking.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from backend.database.connection import get_db_connection, get_db_path, init_connection
from backend.database.schema import init_schema


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class ConversationRepository:
    _initialized = False

    def __init__(self):
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        if not ConversationRepository._initialized:
            db_path = get_db_path()
            conn = init_connection(db_path)
            try:
                init_schema(conn)
                ConversationRepository._initialized = True
            finally:
                conn.close()

    def create_conversation(
        self,
        subject_id: str,
        chat_scope: str,
        persona_id: str,
        chapter_id: Optional[str] = None,
        title: Optional[str] = None,
        initial_state: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Create a new persistent conversation.
        chat_scope must be 'subject' or 'chapter'.
        For 'subject', chapter_id is None.
        For 'chapter', chapter_id must be provided.
        """
        clean_scope = chat_scope.strip().lower()
        if clean_scope not in ("subject", "chapter"):
            raise ValueError(f"Invalid chat_scope '{chat_scope}'. Must be 'subject' or 'chapter'.")

        clean_sub = subject_id.strip().lower()
        clean_chap = chapter_id.strip() if (clean_scope == "chapter" and chapter_id) else None

        conv_id = f"conv_{uuid.uuid4().hex[:12]}"
        now = _utcnow()
        default_title = title or f"{clean_sub.capitalize()} Chat with {persona_id}"
        state_json = json.dumps(initial_state or {
            "explored_moments": [],
            "explored_moment_ids": [],
            "current_moment_id": None,
            "suspended_moment_id": None,
            "interrupted_moment_id": None,
            "quiz_state": None,
        })

        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO conversations (
                    conversation_id, subject_id, chapter_id, chat_scope,
                    persona_id, title, learning_state, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (conv_id, clean_sub, clean_chap, clean_scope, persona_id, default_title, state_json, now, now),
            )

        return self.get_conversation(conv_id)  # type: ignore

    def get_conversation(self, conversation_id: str) -> Optional[dict[str, Any]]:
        """Fetch a conversation by ID, parsing learning_state JSON."""
        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT * FROM conversations WHERE conversation_id = ?",
                (conversation_id,),
            ).fetchone()

        if not row:
            return None

        data = dict(row)
        try:
            data["learning_state"] = json.loads(data["learning_state"])
        except Exception:
            data["learning_state"] = {}
        return data

    def list_conversations(
        self,
        subject_id: Optional[str] = None,
        chat_scope: Optional[str] = None,
        chapter_id: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        List conversations matching filters, ordered by updated_at descending.
        Strictly enforces scope separation:
          - subject chats (chat_scope='subject', chapter_id IS NULL)
          - chapter chats (chat_scope='chapter', chapter_id=?)
        """
        query = "SELECT * FROM conversations WHERE 1=1"
        params: list[Any] = []

        if subject_id:
            query += " AND subject_id = ?"
            params.append(subject_id.strip().lower())

        if chat_scope:
            clean_scope = chat_scope.strip().lower()
            query += " AND chat_scope = ?"
            params.append(clean_scope)

        if chapter_id is not None:
            query += " AND chapter_id = ?"
            params.append(chapter_id.strip())
        elif chat_scope == "subject":
            query += " AND chapter_id IS NULL"

        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)

        with get_db_connection() as conn:
            rows = conn.execute(query, params).fetchall()

        results = []
        for r in rows:
            d = dict(r)
            try:
                d["learning_state"] = json.loads(d["learning_state"])
            except Exception:
                d["learning_state"] = {}
            results.append(d)
        return results

    def update_learning_state(self, conversation_id: str, learning_state: dict[str, Any]) -> bool:
        """Update the structured learning state of a conversation."""
        now = _utcnow()
        state_json = json.dumps(learning_state)
        with get_db_connection() as conn:
            cur = conn.execute(
                "UPDATE conversations SET learning_state = ?, updated_at = ? WHERE conversation_id = ?",
                (state_json, now, conversation_id),
            )
            return cur.rowcount > 0

    def update_title(self, conversation_id: str, title: str) -> bool:
        """Update conversation title."""
        now = _utcnow()
        with get_db_connection() as conn:
            cur = conn.execute(
                "UPDATE conversations SET title = ?, updated_at = ? WHERE conversation_id = ?",
                (title.strip(), now, conversation_id),
            )
            return cur.rowcount > 0

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation and cascade delete its messages."""
        with get_db_connection() as conn:
            cur = conn.execute(
                "DELETE FROM conversations WHERE conversation_id = ?",
                (conversation_id,),
            )
            return cur.rowcount > 0

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        response_format: str = "plain_text",
        response_mode: str = "textbook_grounded",
        citations: Optional[list[dict[str, Any]]] = None,
        suggested_actions: Optional[list[dict[str, Any]]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Add a message to a conversation and bump updated_at."""
        msg_id = f"msg_{uuid.uuid4().hex[:12]}"
        now = _utcnow()
        cit_json = json.dumps(citations or [])
        actions_json = json.dumps(suggested_actions or [])
        meta_json = json.dumps(metadata or {})

        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO messages (
                    message_id, conversation_id, role, content,
                    response_format, response_mode, citations,
                    suggested_actions, created_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    msg_id, conversation_id, role, content,
                    response_format, response_mode, cit_json,
                    actions_json, now, meta_json
                ),
            )
            conn.execute(
                "UPDATE conversations SET updated_at = ? WHERE conversation_id = ?",
                (now, conversation_id),
            )

        return {
            "message_id": msg_id,
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "response_format": response_format,
            "response_mode": response_mode,
            "citations": citations or [],
            "suggested_actions": suggested_actions or [],
            "created_at": now,
            "metadata": metadata or {},
        }

    def get_messages(self, conversation_id: str, limit: int = 100) -> list[dict[str, Any]]:
        """Retrieve conversation messages ordered by created_at ascending."""
        with get_db_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC LIMIT ?",
                (conversation_id, limit),
            ).fetchall()

        results = []
        for r in rows:
            d = dict(r)
            try:
                d["citations"] = json.loads(d["citations"])
            except Exception:
                d["citations"] = []
            try:
                d["suggested_actions"] = json.loads(d["suggested_actions"])
            except Exception:
                d["suggested_actions"] = []
            try:
                d["metadata"] = json.loads(d["metadata"])
            except Exception:
                d["metadata"] = {}
            results.append(d)
        return results

    def get_recent_messages(self, conversation_id: str, limit: int = 4) -> list[dict[str, Any]]:
        """Retrieve the most recent conversation messages ordered chronologically."""
        msgs = self.get_messages(conversation_id, limit=limit)
        return msgs



_repo_instance: Optional[ConversationRepository] = None

def get_conversation_repository() -> ConversationRepository:
    global _repo_instance
    if _repo_instance is None:
        _repo_instance = ConversationRepository()
    return _repo_instance
