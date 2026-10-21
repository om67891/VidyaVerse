# VidyaVerse — Knowledge Retrieval & Persona-Aware Tutoring Report (Part 04)
**Date:** 21 October 2026  
**Implementation Stage:** Part 04 of 05  
**Platform:** Offline-First Learning Hub (VidyaVerse)  
**Hardware Profile:** Local Laptop (8 GB RAM, 4 GB VRAM), Ollama (`qwen3:1.7b`), ChromaDB, SQLite WAL  

---

## 1. Executive Summary

Part 04 successfully connects the Part 01 textbook ingestion pipeline, Part 02 frontend architecture, and Part 03 Persona Intelligence Catalogue into a cohesive, rigorously verified, offline-first educational system across all three subjects:
1. **History:** *Shivachhatrapati*, Standard IV (18 lessons).
2. **Mathematics:** *Mathematics Part II*, Standard X (7 chapters).
3. **Environmental Studies (EVS):** *How We Came to Be*, Standard V (10 chapters).

The system replaces temporary in-memory prototypes with a durable SQLite persistence engine, scope-isolated multi-collection retrieval, deterministic mathematical validation, tap-to-reveal glossary support, and honest progress tracking ("You've explored X of Y learning moments").

---

## 2. Knowledge Retrieval Architecture & Scope Separation

### 2.1 Multi-Collection ChromaDB Topology

Retrieval is handled by a unified, metadata-aware service (`backend/services/retrieval_service.py`), routing requests across three dedicated collections:

| Subject | ChromaDB Collection | Chunk Count | Metadata Fields | Filter Mechanism |
|---|---|---|---|---|
| **History** | `history_master` | 267 | `lesson_number`, `lesson_title`, `pdf_page`, `book_page`, `source` | Chapter: `{"lesson_number": N}`<br>Subject: No filter |
| **Mathematics** | `mathematics_master` | 405 | `chapter_id`, `chapter_number`, `chapter_title`, `pdf_page`, `book_page`, `source` | Chapter: `{"chapter_id": ID}`<br>Subject: No filter |
| **EVS** | `class5_evs_chapters` | 167 | `chapter_id`, `chapter_name`, `page_number`, `source` | Chapter: `{"chapter_id": ID}`<br>Subject: No filter |

### 2.2 Strict Scope Isolation Guarantees

1. **Chapter Scope:** When `chat_scope == "chapter"`, the query vector is filtered strictly using the active chapter's metadata in ChromaDB. Negative tests confirm that querying about outside concepts (e.g., asking about circles while in the Pythagoras chapter) returns **0 chunks** from outside chapters.
2. **Subject Scope:** When `chat_scope == "subject"`, retrieval queries across all chapters within the selected subject without a chapter filter, allowing students to explore cross-lesson concepts seamlessly.
3. **Unindexed / Missing Chapters:** If an unindexed chapter is queried, the service returns an explicit error status (`unindexed_chapter`) rather than silently returning foreign chunks.

---

## 3. Citation & Biographical Accuracy Guardrails

Implemented in `backend/services/citation_validator.py`:

1. **Grounded Citations Only:** Every citation presented to the student must resolve directly to a chunk retrieved for the active turn. Candidate citations referencing unknown chunks or outside chapters are rejected.
2. **Zero False Citations for General Knowledge:** When a student asks a general science, technology, or world knowledge question (e.g., "What is photosynthesis?" or "What is a black hole?"), the system answers conversationally using the model's general knowledge and strips all textbook citations.
3. **Biographical Truth Guardrails:** For historical figures like Chhatrapati Shivaji Maharaj, the validator cross-references family claims against verified ground truth (Father: Shahaji Raje Bhonsale; Mother: Jijabai; Spouses: Saibai, Soyarabai; Birthplace: Shivneri; Oath: Raireshwar; Coronation: Raigad). Hallucinated family members are automatically flagged and corrected.

---

## 4. Deterministic Mathematical Validation

Implemented in `backend/services/math_validator.py` for Standard X Mathematics Part II:

Local small language models (`qwen3:1.7b`) struggle with multi-step geometry and trigonometry arithmetic. A deterministic Python calculation engine validates results independently:
- **Pythagoras Theorem:** $a^2 + b^2 = c^2$, hypotenuse calculation, leg calculation, Pythagorean triplet check (e.g., 3-4-5, 5-12-13, 8-15-17).
- **Special Triangles:** 30°-60°-90° ($side_{30} = \frac{1}{2}c$, $side_{60} = \frac{\sqrt{3}}{2}c$) and 45°-45°-90° ($side_{45} = \frac{1}{\sqrt{2}}c$).
- **Geometric Mean Theorem:** Altitude to hypotenuse $h = \sqrt{seg_1 \times seg_2}$.
- **Apollonius Theorem:** $AB^2 + AC^2 = 2(AM^2 + BM^2) \implies AM = \sqrt{\frac{AB^2+AC^2-2BM^2}{2}}$.
- **Co-ordinate Geometry:** Distance formula $d = \sqrt{(x_2-x_1)^2 + (y_2-y_1)^2}$, midpoint, and slope $m = \frac{y_2-y_1}{x_2-x_1}$.
- **Trigonometry:** Exact values for $\sin, \cos, \tan$ at 0°, 30°, 45°, 60°, 90°.
- **Mensuration:** Cylinder ($V=\pi r^2 h$, $CSA=2\pi r h$), Cone ($l=\sqrt{r^2+h^2}$, $V=\frac{1}{3}\pi r^2 h$), Sphere ($V=\frac{4}{3}\pi r^3$), Sector area and arc length.

---

## 5. Curriculum Learning Maps & Progress Tracking

Implemented in `backend/services/learning_map_service.py`:
- Structured learning maps for all 18 History lessons, 7 Mathematics chapters, and 10 EVS chapters.
- Each chapter defines 5–8 stable learning moments (`moment_id`), key facts, and clear completion conditions.
- Progress engine calculates honest exploration:
  $$\text{Progress} = \frac{\text{Explored Moments}}{\text{Total Moments}} \times 100\%$$
- Emits user-friendly progress displays, e.g., *"You've explored 3 of 7 learning moments"*, along with the next recommended moment.

---

## 6. Glossary Service & Tap-to-Reveal Definitions

Implemented in `backend/services/glossary_service.py`:
- Registered textbook definitions for key terms across History (*Swaraj*, *Chhatrapati*, *Ghanimikava*, *Watandar*, *Abhanga*), Mathematics (*Hypotenuse*, *Pythagorean Triplet*, *Similar Triangles*, *Tangent*, *Angle of Elevation*), and EVS (*Evolution*, *Homo habilis*, *Microliths*, *Stratigraphy*).
- Automatic term detection in answer text allows the frontend to underline terms and show child-friendly popover definitions without triggering full page reloads or scope changes.

---

## 7. Interactive Quizzes & Security

Implemented in `backend/services/quiz_service.py`:
- Curated chapter quizzes based on verified textbook questions and calculations.
- **Client Security:** Public endpoints (`GET /api/quiz/...`) return `StudentQuizQuestion` without the `correct_index` field, preventing cheating via browser devtools.
- **Deterministic Validation:** `POST /api/quiz/validate` checks answers on the server and returns constructive pedagogical explanations.
