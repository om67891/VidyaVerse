# VidyaVerse — Persistent Conversation Management Report (Part 04)
**Date:** 21 October 2026  
**Implementation Stage:** Part 04 of 05  
**Platform:** Offline-First Learning Hub (VidyaVerse)  
**Database:** SQLite 3 with Write-Ahead Logging (WAL) Mode  
**Database Path:** `data/vidyaverse.db`  

---

## 1. Storage Architecture & Backend Choice

VidyaVerse operates on an offline laptop without cloud dependencies or heavyweight relational database servers. 

Part 04 migrates all conversation, message, and learning state persistence from temporary in-memory stores to an ACID-compliant local **SQLite** database at `data/vidyaverse.db`.

### 1.1 Concurrency & Connection Settings

Configured in `backend/database/connection.py`:
- `PRAGMA foreign_keys = ON;` — Enforces referential integrity between conversations and messages.
- `PRAGMA journal_mode = WAL;` — Write-Ahead Logging enables concurrent reads while writes are committed.
- `PRAGMA synchronous = NORMAL;` — Optimal balance between durability and write latency on local flash storage.
- Auto-creation of directory `data/` on startup.

---

## 2. Database Schema & Indexes

Defined in `backend/database/schema.py`:

```sql
CREATE TABLE IF NOT EXISTS conversations (
    conversation_id TEXT PRIMARY KEY,
    subject_id TEXT NOT NULL,
    chapter_id TEXT,
    chat_scope TEXT NOT NULL CHECK(chat_scope IN ('subject', 'chapter')),
    persona_id TEXT NOT NULL,
    title TEXT NOT NULL,
    learning_state TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    message_id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    response_format TEXT NOT NULL DEFAULT 'plain_text',
    response_mode TEXT NOT NULL DEFAULT 'textbook_grounded',
    citations TEXT NOT NULL DEFAULT '[]',
    suggested_actions TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    metadata TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id) ON DELETE CASCADE
);

-- Fast filtered history indexing
CREATE INDEX IF NOT EXISTS idx_conversations_filter
ON conversations(subject_id, chat_scope, chapter_id, updated_at DESC);

-- Chronological message retrieval
CREATE INDEX IF NOT EXISTS idx_messages_conversation_order
ON messages(conversation_id, created_at ASC);
```

---

## 3. Scope Isolation & Independent Histories

Per Section 19.2 of the specification, subject-wide chats and chapter-specific chats maintain strictly independent history streams:

1. **Subject Chat:** `chat_scope == "subject"`, `chapter_id IS NULL`.
2. **Chapter Chat:** `chat_scope == "chapter"`, `chapter_id == <valid_chapter_id>`.

The repository method `list_conversations(subject_id, chat_scope, chapter_id)` enforces these conditions. Mathematics Chapter 2 chats never leak into Chapter 1 sidebars, nor do subject-wide chats appear inside specific chapter views.

---

## 4. Persona Locking & Immutability

Once a conversation is created with a selected persona (e.g. `pythagoras`, `charles_darwin`, or `shivaji_maharaj`), that persona identity is locked in the `conversations` record. Subsequent student messages cannot change the persona in place; opening a new conversation is required to converse with a different persona.

---

## 5. Learning State & Interruption Recovery

The `learning_state` field persists:
- `explored_moment_ids`: List of stable moment IDs completed during the conversation.
- `current_moment_id`: Active learning moment being explored.
- `suspended_moment_id`: When a student asks a custom question during a guided moment or story, the prior moment ID is recorded as suspended. The tutoring engine automatically offers a `"Return to previous lesson stage"` action, allowing students to resume without losing their place.

---

## 6. Server Restart Survival Verification

Persistence was tested in `scripts/test_part4_persistence.py` by:
1. Creating chapter and subject conversations and populating messages and learning states.
2. Terminating active connections and closing the repository instance.
3. Spawning a fresh repository instance in a new process to simulate an application restart.
4. Confirming that all conversations, message orderings, structured citations, actions, and explored moments were restored with 100% accuracy.
