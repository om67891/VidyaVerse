# Class 5 Learning Hub — Educational Chatbot POC

A local, AI-powered educational tutor designed for Class 5 students. Features a Google Classroom-inspired subject dashboard, chapter navigator, and a ChatGPT-inspired conversational tutor using subtle neumorphism, strict chapter-isolated textbook RAG (`multilingual-e5-small` + ChromaDB), and local LLM generation (`qwen3:1.7b` via Ollama).

---

## 🌟 Key Features & Improvements

### 1. Generic Chapter-Aware RAG & Overview Strategy
- **Chapter-Aware First-Class Pipeline:** Tracks selected `chapter_id`, `chapter_title`, bounded history, original student instruction, rewritten retrieval query, mode, and verified evidence metadata.
- **Generic Chapter Overview Retrieval:** When questions request chapter overviews, summaries, main topics, or chapter importance (e.g. *"What are the 3 main topics taught in this chapter?"*, *"Why is this chapter important for us to study?"*), the pipeline combines opening outline chunks (headings, outlines) with top semantic chunks strictly from the selected chapter.
- **Anti-Poisoning Conversation Resolution:** Anaphoric and elliptical follow-ups (*"Explain the second one"*, *"Give me 10 bullet points"*, *"Add more"*) preserve their previous subject, while queries mentioning *"this chapter"* or asking for chapter overviews/roleplays always ground in the active chapter rather than inheriting previous off-topic queries.
- **Roleplay Grounding:** Chapter roleplays (*"Act like a scientist or researcher studying the topic of this chapter"*) adopt first-person narration grounded strictly in the selected chapter's artifacts, tools, and evidence (e.g. Neolithic tools, pottery, ancient settlements in Chapter 9), completely isolated from previous turns (such as questions about smartphones).

### 2. Honest Textbook Coverage & Zero False Citations
- **Textbook Absence Detection:** Detects whether a queried topic (e.g. smartphones, internet, social workers) is discussed in the selected chapter using substantive keyword presence and distance thresholds.
- **Honest Answers:** Directly states that the chapter does not cover the topic, explains what the chapter actually covers, and attaches strictly **0 false citations**.
- **Cross-Chapter Topic Isolation:** When historical sources (*"material, written, and oral sources"*) are queried on Chapter 9 (*Settled Life and Urban Civilization*), the pipeline routes to general knowledge with **0 Chapter 9 citations** because the topic is not covered in Chapter 9. On Chapter 1 (*What is History?*), it retrieves the authentic textbook passages and page citations.

### 3. Factual Accuracy in General Knowledge (Generic, Zero Hardcoding)
- **Generic Constraint Compliance:** System instructions enforce strict adherence to geographic, temporal, and categorical boundaries in the student's request.
- **Indian Rivers Test:** For *"Name 4 famous rivers in India"*, the model reliably names genuine Indian rivers (e.g., Ganges, Brahmaputra, Indus, Cauvery/Godavari/Narmada) with zero foreign hallucinations (no Nile or Amazon) and zero textbook citations.
- **Generic List Continuation:** *"Add more"* follow-ups provide brand-new items strictly in the same category without duplicating previous responses.

### 4. Markdown Formatting Integrity
- **Clean Numbering & Spacing:** Numbered list items are rendered on separate lines with clear spacing (`1. `, `2. `) and bold title formatting.
- **Markdown Headings:** Headers (`### `, `## `, `# `) are parsed into styled headers without raw hash marks or broken line breaks.
- **Minimal Output Sanitization:** Thinking tags (`<think>...</think>`), leading role labels, and repetitive catchphrases are cleanly removed without joining lines or mangling Unicode text.

### 5. Google Classroom & ChatGPT-Inspired UI
- **Light Neumorphic Aesthetic:** Slate background (`#F8FAFC`) with soft raised card shadows, gently inset inputs, and crisp educational accents (Emerald green `#10B981`, Sky blue `#0284C7`).
- **Subject Dashboard:** 10 EVS chapters fully indexed and AI-ready; demo subjects clearly marked *"Coming soon"*.
- **ChatGPT-Inspired Chat Interface:** Max-width viewport layout (`880px`), responsive message bubbles, sticky composer with `Enter` to send, verified textbook citation chips, and distinct mode badges.

---

## 🏗️ Project Architecture

```
ChatBot_POC/
├── backend/
│   ├── config.py              # Pydantic v2 configuration & env loader
│   ├── schemas.py             # Pydantic request/response schemas
│   ├── main.py                # FastAPI endpoints & CORS
│   └── services/
│       ├── catalog.py         # PDF scanner & chapter metadata catalog
│       ├── indexing.py        # PDF chunking (500 tokens / 50 overlap) & embedding
│       └── rag.py             # Generic overview strategy, router, query resolver, retrieval & Ollama client
├── frontend/
│   ├── app/
│   │   ├── page.tsx           # Google Classroom subject dashboard
│   │   ├── subjects/[subjectId]/page.tsx # Chapter selection topic rows
│   │   ├── chat/[chapterId]/page.tsx     # ChatGPT-inspired chat interface with markdown rendering
│   │   ├── globals.css        # Light neumorphic design tokens & responsive styles
│   │   └── layout.tsx         # Root layout with Inter font
│   ├── lib/api.ts             # Typed API client
│   └── types/index.ts         # Shared TypeScript definitions
├── Environmental Studies/     # 10 Class 5 EVS chapter PDFs
├── vectorstore/               # Persistent ChromaDB (167 chunks across 10 chapters)
├── a.ipynb                    # Synchronized Jupyter inspection notebook (28 cells)
├── test_poc.py                # Comprehensive regression test suite (Cases A through I)
└── README.md                  # This documentation
```

---

## ⚙️ Prerequisites

| Dependency | Required Version | Verification Command |
|---|---|---|
| **Python** | 3.12+ | `python --version` |
| **Node.js** | 20+ (Node 22 used) | `node --version` |
| **Ollama** | Latest | `ollama --version` |
| **Model** | `qwen3:1.7b` | `ollama list` |

---

## 🚀 Quick Start (Windows PowerShell)

Run all commands from the repository root: `c:\Users\spyte\Desktop\ChatBot_POC`

### 1. Ensure Ollama is Running with Qwen3
In PowerShell:
```powershell
# Confirm Ollama service is active
ollama list

# If qwen3:1.7b is not downloaded:
ollama pull qwen3:1.7b
```

### 2. Start the Backend API Server
In PowerShell:
```powershell
.venv\Scripts\uvicorn.exe backend.main:app --reload --port 8000
```
- API Base URL: `http://localhost:8000`
- Interactive Swagger Docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/health`

### 3. Start the Frontend Development Server
In a **new** PowerShell window:
```powershell
cd frontend
npm run dev
```
- Web Application: `http://localhost:3000`

### 4. Build Frontend for Production (Verification)
```powershell
cd frontend
npm run build
```

---

## 🧪 Automated Testing & Verification

Run the end-to-end regression test suite against the running backend and Ollama:

```powershell
.venv\Scripts\python.exe test_poc.py
```

### Regression Test Cases Covered (Cases A through I):
1. **Prerequisite Check:** Backend health and Ollama connectivity (`qwen3:1.7b`).
2. **Case A (Chapter Overview):** Ch 9 `"What are the 3 main topics taught in this chapter?"` → Answers from Chapter 9 indexed outline (metals, potter's wheel, trade & transport); zero freedom fighter / Constitution contamination; verified Chapter 9 citations.
3. **Case B (Chapter Importance):** Ch 9 `"Why is the topic of this chapter important for us to study?"` → Grounded in settled life, tools, early civilization.
4. **Case C (Chapter-Aware Roleplay Anti-Poisoning):** Roleplay as scientist studying Chapter 9 after asking about smartphones → Answers in first person focusing on ancient artifacts and settlements; zero mention of smartphones or internet.
5. **Case D (Chapter Coverage & Absence):** Ch 9 `"What does this chapter say about how smartphones and the internet were invented?"` → Honestly explains absence from Chapter 9; strictly 0 citations.
6. **Case E (General Knowledge Rivers):** `"Name 4 famous rivers in India."` → 100% genuine Indian rivers (Ganga, Brahmaputra, Indus, Cauvery); zero foreign rivers (no Nile, Amazon); 0 textbook citations.
7. **Case F (Historical Sources Isolation):** Queries historical sources on Chapter 9 (routes to general knowledge, 0 Chapter 9 citations) vs Chapter 1 (routes to `chapter_question` with Chapter 1 citations).
8. **Case G (Markdown Integrity):** Numbered list items on separate lines with clear spacing and bold formatting.
9. **Case H (Strict Chapter Isolation):** Chapter 1 vs Chapter 9 retrieval isolation with zero cross-chapter pollution.
10. **Case I (Existing Regressions):**
    - Subtest I-1: Casual greeting (`"Hii"`) → `general_chat`, 0 citations.
    - Subtest I-2: Chapter 1 summary → `chapter_question`, verified Chapter 1 citations.
    - Subtest I-3: Contextual follow-up (`"Give me bullet points, at least 10."`) → `chapter_question`, at least 10 bullet items.
    - Subtest I-4: Detailed follow-up (`"Explain black holes"` → `"Give me a detailed answer"`) → `general_knowledge`, 0 citations.
    - Subtest I-5: List continuation (`"Add more"`) → Continues without repeating earlier items.
    - Subtest I-6: Chapter 1 absence (`"Which social workers are mentioned in this chapter?"`) → Honest absence, 0 citations.
    - Subtest I-7: Persona roleplay (`"Act like Shivaji Maharaj..."`) → First person, 0 fake citations.
    - Subtest I-8: Chapter 3 Chronology (`(d) -> (b) -> (a) -> (c)`).
    - Subtest I-9: Diagnostics endpoint verification.

---

## 📓 Interactive Diagnostics Notebook (`a.ipynb`)

`a.ipynb` provides an interactive inspection environment (28 runnable cells):
- **Cells 1–16:** PDF text extraction, document chunking, ChromaDB collection status, and initial checks.
- **Cell 17:** 4-Way Intent Routing verification (`general_chat`, `chapter_question`, `general_knowledge`, `chapter_plus_general`).
- **Cell 18:** Follow-up List Resolution Test (`"Explain the second one"`).
- **Cell 19:** Chapter 3 Chronology Verification (`(d) -> (b) -> (a) -> (c)`).
- **Cell 20:** Developer diagnostics inspection (`get_diagnostics()`).
- **Cell 21:** Contextual Follow-up (10 Bullet Points).
- **Cell 22:** General Knowledge Detail Expansion (Black holes -> Detailed).
- **Cell 23:** Continue a List without Repetition (Freedom fighters -> Add more).
- **Cell 24:** Textbook Coverage Absence Check (Social workers -> 0 citations).
- **Cell 25:** Educational Roleplay (Shivaji Maharaj -> First Person).
- **Cell 26:** Chapter 9 Overview & Anti-Poisoning Check.
- **Cell 27:** General Knowledge Factual Accuracy (Rivers in India).

To open the notebook:
```powershell
.venv\Scripts\jupyter-lab.exe a.ipynb
```

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Backend and Ollama status check |
| `GET` | `/api/subjects` | All subjects with chapter count and demo status |
| `GET` | `/api/subjects/{id}/chapters` | Chapters for a subject with indexing status |
| `GET` | `/api/chapters/{id}` | Detailed chapter metadata |
| `POST` | `/api/chat` | Send a chat message with chapter context and history |
| `GET` | `/api/index/status` | Current ChromaDB vector store statistics |
| `POST` | `/api/index` | Trigger indexing pipeline |
| `GET` | `/api/dev/diagnostics` | Developer endpoint for retrieval inspection |

### Chat Request Payload
```json
{
  "chapter_id": "EVS_CH09",
  "message": "What are the 3 main topics taught in this chapter?",
  "history": [],
  "mode": "study"
}
```

### Chat Response Payload
```json
{
  "answer": "The three main topics taught in this chapter are:\n\n1. **Use of metals** – How people used copper, stone, and iron tools...\n2. **Pots made on the potter’s wheel** – How pottery was made using the wheel...\n3. **Trade and transport** – How people traded goods across settlements...",
  "sources": [
    {
      "chapter_title": "Settled Life and Urban Civilization",
      "pdf_filename": "Chapter 9 - Settled Life and Urban Civilization.pdf",
      "page_number": 1
    }
  ],
  "mode": "chapter_question",
  "retrieved_count": 5
}
```

# VidyaVerse
