"""
Repository for faculty-uploaded learning resources and textbooks.
Provides transactional CRUD operations on the uploaded_resources SQLite table.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any, Optional

from backend.database.connection import get_db_connection, get_db_path, init_connection
from backend.database.schema import init_schema


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class UploadedResourceRepository:
    _initialized = False

    def __init__(self):
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        if not UploadedResourceRepository._initialized:
            db_path = get_db_path()
            conn = init_connection(db_path)
            try:
                init_schema(conn)
                UploadedResourceRepository._initialized = True
            finally:
                conn.close()

    def create_resource(
        self,
        resource_id: str,
        subject_id: str,
        class_number: int,
        chapter_id: str,
        chapter_number: int,
        chapter_name: str,
        original_filename: str,
        stored_path: str,
        file_hash: str,
        file_size_bytes: int,
        processing_status: str = "uploaded",
        source_type: str = "faculty_upload",
    ) -> dict[str, Any]:
        """Insert a new uploaded resource record."""
        now = _utcnow()
        clean_sub = subject_id.strip().lower()

        sql = """
        INSERT INTO uploaded_resources (
            resource_id, subject_id, class_number, chapter_id, chapter_number,
            chapter_name, source_type, original_filename, stored_path, file_hash,
            file_size_bytes, processing_status, chunk_count, error_message,
            created_at, updated_at, indexed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, NULL, ?, ?, NULL);
        """
        with get_db_connection() as conn:
            conn.execute(
                sql,
                (
                    resource_id,
                    clean_sub,
                    class_number,
                    chapter_id,
                    chapter_number,
                    chapter_name.strip(),
                    source_type,
                    original_filename,
                    stored_path,
                    file_hash,
                    file_size_bytes,
                    processing_status,
                    now,
                    now,
                ),
            )
        return self.get_resource(resource_id)  # type: ignore

    def update_status(
        self,
        resource_id: str,
        status: str,
        chunk_count: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """Update processing status, chunk count, or error message."""
        now = _utcnow()
        indexed_at = now if status == "indexed" else None

        sql = """
        UPDATE uploaded_resources
        SET processing_status = ?,
            chunk_count = COALESCE(?, chunk_count),
            error_message = ?,
            indexed_at = COALESCE(?, indexed_at),
            updated_at = ?
        WHERE resource_id = ?;
        """
        with get_db_connection() as conn:
            conn.execute(sql, (status, chunk_count, error_message, indexed_at, now, resource_id))

        return self.get_resource(resource_id)

    def get_resource(self, resource_id: str) -> Optional[dict[str, Any]]:
        """Retrieve a single resource by its resource_id."""
        sql = "SELECT * FROM uploaded_resources WHERE resource_id = ?;"
        with get_db_connection() as conn:
            row = conn.execute(sql, (resource_id,)).fetchone()
            if row:
                return dict(row)
        return None

    def get_resource_by_chapter_id(self, chapter_id: str) -> Optional[dict[str, Any]]:
        """Retrieve a resource by chapter_id (case-insensitive)."""
        sql = "SELECT * FROM uploaded_resources WHERE LOWER(chapter_id) = LOWER(?);"
        with get_db_connection() as conn:
            row = conn.execute(sql, (chapter_id.strip(),)).fetchone()
            if row:
                return dict(row)
        return None

    def list_resources(
        self,
        subject_id: Optional[str] = None,
        class_number: Optional[int] = None,
        status: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """List uploaded resources with optional filters."""
        sql = "SELECT * FROM uploaded_resources WHERE 1=1"
        params: list[Any] = []

        if subject_id:
            sql += " AND LOWER(subject_id) = LOWER(?)"
            params.append(subject_id.strip())
        if class_number is not None:
            sql += " AND class_number = ?"
            params.append(class_number)
        if status:
            sql += " AND processing_status = ?"
            params.append(status.strip())

        sql += " ORDER BY chapter_number ASC, created_at DESC;"

        with get_db_connection() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]

    def delete_resource(self, resource_id: str) -> bool:
        """Delete an uploaded resource record."""
        sql = "DELETE FROM uploaded_resources WHERE resource_id = ?;"
        with get_db_connection() as conn:
            cur = conn.execute(sql, (resource_id,))
            return cur.rowcount > 0

    def check_conflict(
        self,
        subject_id: str,
        class_number: int,
        chapter_number: int,
        chapter_id: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """Check if an active upload already exists for this subject, class, and chapter number."""
        clean_sub = subject_id.strip().lower()
        sql = """
        SELECT * FROM uploaded_resources
        WHERE LOWER(subject_id) = LOWER(?)
          AND class_number = ?
          AND chapter_number = ?
          AND processing_status IN ('uploaded', 'processing', 'indexed')
        """
        params: list[Any] = [clean_sub, class_number, chapter_number]
        if chapter_id:
            sql += " AND chapter_id != ?"
            params.append(chapter_id.strip())

        sql += " LIMIT 1;"
        with get_db_connection() as conn:
            row = conn.execute(sql, params).fetchone()
            if row:
                return dict(row)
        return None


# Global singleton repository
_uploaded_repo: Optional[UploadedResourceRepository] = None


def get_uploaded_resource_repository() -> UploadedResourceRepository:
    global _uploaded_repo
    if _uploaded_repo is None:
        _uploaded_repo = UploadedResourceRepository()
    return _uploaded_repo
