# Developer Practical Handoff Guide
**Project:** Learning Hub / VidyaVerse (Offline-First Educational Platform)  
**Location:** `reports/DEVELOPMENT_HANDOFF.md`  
**Reference Reports:** [TEXTBOOK_INGESTION_REPORT.md](file:///c:/Users/spyte/Desktop/ChatBot_POC/reports/TEXTBOOK_INGESTION_REPORT.md), [FRONTEND_IMPLEMENTATION_REPORT.md](file:///c:/Users/spyte/Desktop/ChatBot_POC/reports/FRONTEND_IMPLEMENTATION_REPORT.md), [PERSONA_IMPLEMENTATION_REPORT.md](file:///c:/Users/spyte/Desktop/ChatBot_POC/reports/PERSONA_IMPLEMENTATION_REPORT.md), [PERSONA_EVALUATION_RESULTS.md](file:///c:/Users/spyte/Desktop/ChatBot_POC/reports/PERSONA_EVALUATION_RESULTS.md)  
**Date:** October 21, 2026  
**Implementation Stage:** Part 01, Part 02 & Part 03 Complete — Ready for Part 04 (Adaptive Tutoring & Retrieval Progression)

---

## 1. Quick Start Commands (PowerShell)

### Terminal 1: Start Backend (FastAPI on Port 8000)
```powershell
cd C:\Users\spyte\Desktop\ChatBot_POC
.\.venv\Scripts\uvicorn.exe backend.main:app --port 8000 --reload
```
- Health Check: `http://localhost:8000/api/health`
- Subjects API: `http://localhost:8000/api/subjects`
- Personas API: `http://localhost:8000/api/personas` (Supports `?subject_id=` and `?chapter_id=`)
- Single Persona API: `http://localhost:8000/api/personas/{persona_id}`
- Chat Endpoint: `POST http://localhost:8000/api/chat`
- Swagger Docs: `http://localhost:8000/docs`

### Terminal 2: Start Frontend (Next.js on Port 3000)
```powershell
cd C:\Users\spyte\Desktop\ChatBot_POC\frontend
npm run dev
```
- Classroom Dashboard: `http://localhost:3000`
- History Dashboard: `http://localhost:3000/subjects/history`
- Mathematics Dashboard: `http://localhost:3000/subjects/mathematics`
- EVS Dashboard: `http://localhost:3000/subjects/evs`
- Scoped Chapter Chat: `http://localhost:3000/chat/{chapterId}?persona={personaId}`
- Scoped Subject Studio Chat: `http://localhost:3000/chat/subject/{subjectId}?persona={personaId}`

### Terminal 3: Verify Ollama Service
```powershell
ollama list
# Ensure qwen3:1.7b is listed
# If not running: ollama serve
```

---

## 2. Verification Commands

### 1. Ingestion Pipeline & Boundary Verification (Part 01)
```powershell
cd C:\Users\spyte\Desktop\ChatBot_POC
.\.venv\Scripts\python.exe -m scripts.textbooks.segment_textbook --validate-only
.\.venv\Scripts\python.exe -m scripts.textbooks.run_textbook_ingestion
```

### 2. Persona Schema & Profile Validation (Part 03)
```powershell
cd C:\Users\spyte\Desktop\ChatBot_POC
.\.venv\Scripts\python.exe scripts/validate_personas.py
```
*Expected Result:* 24/24 personas valid, 72/72 examples valid, 0 errors.

### 3. Persona Intelligence Evaluation Suite (Part 03)
```powershell
cd C:\Users\spyte\Desktop\ChatBot_POC
.\.venv\Scripts\python.exe scripts/evaluate_personas.py
```
*Expected Result:* 120/120 test cases passed (100% PASS across all 5 evaluation dimensions).

### 4. Frontend Production Build Check
```powershell
cd C:\Users\spyte\Desktop\ChatBot_POC\frontend
npx tsc --noEmit
npm run build
```
*Expected Result:* 0 TypeScript errors, all routes generated.

### 5. Existing Prototype & RAG Regression Suites
```powershell
cd C:\Users\spyte\Desktop\ChatBot_POC
.\.venv\Scripts\python.exe test_history_prototype.py
.\.venv\Scripts\python.exe test_poc.py
```

---

## 3. Authoritative Directory & File Structure

```text
ChatBot_POC/
│
├── History/
│   ├── History.pdf                          # Master complete textbook (Std IV, 92 pp)
│   ├── chapters/                            # 18 validated chapter PDFs
│   │   ├── chapter_01_maharashtra_before_shivaji.pdf
│   │   └── ... chapter_18_welfare_state_of_swaraj.pdf
│   └── metadata/
│       └── chapter_manifest.json            # 18-chapter manifest with 1-based page citations
│
├── Maths/
│   ├── Mathematics.pdf                      # Master complete textbook (Std X, 180 pp)
│   ├── chapters/                            # 7 validated chapter PDFs
│   │   ├── chapter_01_similarity.pdf
│   │   └── ... chapter_07_mensuration.pdf
│   └── metadata/
│       └── chapter_manifest.json            # 7-chapter manifest with 1-based page citations
│
├── Environmental Studies/
│   ├── EVS_Complete.pdf                     # Master complete textbook (Std V, 66 pp)
│   ├── Chapter 1 - What is History.pdf ...  # 10 legacy chapter files preserved
│   ├── chapters/                            # 10 standardized validated chapter PDFs
│   │   ├── chapter_01_what_is_history.pdf
│   │   └── ... chapter_10_historic_period.pdf (repaired: 8 pp, back-matter omitted)
│   └── metadata/
│       └── chapter_manifest.json            # 10-chapter manifest with 1-based page citations
│
├── persona_character_pack/
│   └── persona_pack/
│       ├── MANIFEST.json
│       ├── PERSONA_CHARACTER_BIBLE.md
│       └── personas/
│           ├── catalog.json                 # 24 registered personas (8 History, 8 Maths, 8 EVS)
│           ├── history/                     # Individual persona specification files
│           ├── mathematics/
│           └── evs/
│
├── backend/
│   ├── main.py                              # FastAPI routes for subjects, chapters, personas, chat
│   ├── schemas.py                           # ChapterSchema, SubjectSchema, PersonaSchema
│   └── services/
│       ├── catalog.py                       # Manifest-driven subject & chapter provider
│       ├── rag.py                           # Chapter-isolated RAG engine with ChromaDB
│       ├── history_service.py               # History guided conversational storyteller
│       └── history_map.py                   # 18-lesson curriculum map
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx                         # Classroom Dashboard (Subject cards, Continue Learning)
│   │   ├── subjects/[subjectId]/page.tsx    # Split Subject Dashboard (Cover Left, Chapters Right)
│   │   ├── subjects/[subjectId]/chapters/[chapterId]/page.tsx # Chapter Overview & SVG Diagrams
│   │   ├── chat/[chapterId]/page.tsx        # Chapter-wise scoped chat interface
│   │   ├── chat/subject/[subjectId]/page.tsx# Subject-wide scoped chat interface
│   │   └── subjects/history/story/page.tsx  # Dedicated Shivaji guided storyteller route
│   ├── components/
│   │   ├── Navbar.tsx                       # Global header with offline health status
│   │   ├── personas/PersonaSelectionModal.tsx# Reusable persona guide selector
│   │   └── history/HistoryExperience.tsx    # Preserved History storyteller prototype
│   └── public/
│       ├── covers/                          # Authentic extracted covers (History, Maths, EVS)
│       └── avatars/                         # Local persona avatars
│
├── scripts/
│   └── textbooks/                           # Reusable modular textbook ingestion pipeline
│       ├── discover_textbooks.py
│       ├── inspect_pdf.py
│       ├── extract_chapter_boundaries.py
│       ├── segment_textbook.py
│       ├── validate_chapter_pdfs.py
│       ├── run_textbook_ingestion.py
│       └── README.md
│
└── reports/
    ├── TEXTBOOK_INGESTION_REPORT.md         # Part 01 execution findings
    ├── FRONTEND_IMPLEMENTATION_REPORT.md    # Part 02 frontend redesign findings
    └── DEVELOPMENT_HANDOFF.md               # This document
```

---

## 4. Frontend-Backend Contract for Next Implementation Phases

1. **Manifest-Driven Data Source:**
   - The frontend never hardcodes chapter lists. It consumes `GET /api/subjects/{id}` which derives directly from `chapter_manifest.json`.
2. **Persona Integration:**
   - `GET /api/personas?subject_id={sub}&chapter_id={ch}` returns registered personas ordered with topic relevance first.
   - Selected `persona_id` is passed as a query param (`?persona={id}`) and locked for the conversation.
3. **Chat Scoping:**
   - Subject-wide chat: `/chat/subject/[subjectId]` covers the entire textbook curriculum.
   - Chapter-wise chat: `/chat/[chapterId]` performs isolated chapter learning and retrieval.
4. **Offline Resilience:**
   - All assets (covers, avatars, SVG diagrams, PDFs) are 100% local. Zero external cloud APIs required.

---

## 5. Next Steps for Part 03 (Persona Catalogue and Behaviour Rules)

- Complete persona profile authoring and knowledge boundaries using `persona_character_pack/persona_pack/personas/catalog.json`.
- Implement specific pedagogical behavior contracts for the 8 Mathematics coaches (proof step derivations, diagram explanations).
- Implement specific scientific and archaeological reasoning contracts for the 8 EVS guides.
- Implement authoritative backend persona prompt builders.
