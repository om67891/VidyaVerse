# Interactive History Learning Hub — Test Plan

**Target Product:** Class 4/5 Interactive History Learning Prototype (*Shivachhatrapati*)  
**Architecture:** Next.js (React 19, TypeScript), FastAPI (Python 3.12), ChromaDB (Vector Store), Ollama (`qwen3:1.7b`), Multilingual-E5-Small  
**Hardware Environment:** 8 GB System RAM, 4 GB GPU VRAM (NVIDIA RTX 2050), Local NVMe Storage (1.30 GB free)

---

## 1. Test Objectives & Scope

1. **First-Person Storyteller & Persona Continuity (P1–P4):**
   - Chhatrapati Shivaji Maharaj serves as the primary educational storyteller throughout the curriculum, including background heritage lessons (Lesson 1, Lesson 2, Lesson 3, Lesson 5) where he guides as a wise historical narrator without claiming false eyewitness presence to pre-1630 events.
   - Consistent portrait avatar (`/avatars/shivaji-maharaj.png`) and role badges.

2. **Stage-Aware Contextual Interaction (I1–I6):**
   - Elimination of the generic, repetitive 4-choice menu (`["Explore figures & details", "Explain in simpler words", "Take the knowledge check", "Move to next lesson"]`).
   - Replaced with topic-specific, curriculum-grounded stage choices that advance the structured learning loop: *Narrate → Pause Point → Age-appropriate question/decision → Contextual choices → Student reaction → Explanatory feedback → Story continuation*.

3. **Custom-Question Continuity & Interruption (C1–C6):**
   - Student can ask custom questions at any stage via the persistent bottom composer.
   - Answers are delivered in the same timeline.
   - Previous lesson stage and choice options are preserved in `session.saved_state`.
   - Clicking "Return to Story" smoothly resumes the exact prior stage without repetition or progress reset.
   - General knowledge questions (e.g., photosynthesis) receive natural answers with 0 false history citations.

4. **Textbook Grounding & Whole-Book RAG (R1–R6):**
   - 267 indexed chunks from master `History/History.pdf` across all 18 lessons.
   - Deduplicated, verified citations reflecting real PDF and book page numbers.

5. **Adaptive Structured Formats (F1–F17):**
   - Typed responses: `story`, `explanation`, `figure` (`FigureProfile`), `timeline` (`TimelineEvent`), `cause_effect` (`CauseEffectData`), `comparison` (`ComparisonData`), `quiz` (`QuizCheck`), `recap` (`recap_points`), and `chat`.

6. **Deterministic Quiz Evaluation & Progression (Q1–Q5):**
   - Deterministic answer validation on backend (index comparison).
   - Instant pedagogical feedback (positive reinforcement or constructive clue).
   - Lesson completion registered only upon correct quiz submission.

7. **Lightweight Local Visual Storytelling:**
   - Safe offline curated vector illustration pipeline (`backend/services/generate_history_illustrations.py`).
   - SVG assets in `frontend/public/illustrations/history/` with `manifest.json`.
   - Zero OOM risk; no 4GB diffusion model loaded simultaneously in VRAM.

---

## 2. Test Matrix & Scenarios

| Test ID | Category | Scenario | Expected Behavior |
|:---|:---|:---|:---|
| **P1** | Storyteller | Start Lesson 2 (Work of the Saints) | Shivaji Maharaj is primary storyteller; avatar `/avatars/shivaji-maharaj.png`; badge "Roleplay". |
| **P2** | Authenticity | Historical accuracy of pre-1630 narration | No claims of having met Sant Dnyaneshwar in 1290 or being born before 1630. |
| **P3** | Persona Continuity | Switch across multiple lessons (L1, L2, L4, L9) | Speaker identity and avatar remain consistently Shivaji Maharaj. |
| **P4** | Topic Adaptation | Compare opening narrations of L1 vs L2 vs L9 | Contextually tailored narration for each chapter's historical content. |
| **I1** | Meaningful Choices | Advance through Lesson 2 stages | Choices directly reflect current historical figures (Dnyaneshwar, Tukaram, Ramdas). |
| **I2** | Menu Diversity | Compare choices between Stage 1 and Stage 2 | Distinct choices; zero appearance of the legacy 4-choice generic menu. |
| **I3** | Choice Execution | Click "Meet Sant Dnyaneshwar of Alandi" | Triggers figure profile stage; displays biography, place, Pasaydan teachings. |
| **I4** | Tutor Progression | Advance without manual typing | Step-by-step learning loop with pause prompt and next actions. |
| **I5** | Student Agency | Explore optional branch and return | Branch explored with dedicated card; return path to story provided. |
| **I6** | Lesson Completion | Submit correct quiz answer | Awards lesson completion; registers in `completed_lessons`; offers next lesson. |
| **C1** | Interruption | Ask custom question during story narration | Answered inline in the conversation timeline; lesson stage saved. |
| **C2** | Resumption | Click "Return to Story" after custom question | Resumes exact paused stage with previous choices intact. |
| **C3** | Pronouns | Ask "how strong you were" | Resolves "you" to Shivaji Maharaj; cites martial training/Pratapgad pages. |
| **C4** | General Knowledge | Ask "What is photosynthesis?" | Natural scientific explanation; 0 false History citations attached. |
| **C5** | Scope Honesty | Ask "What does textbook say about dinosaurs?" | Honestly states topic is outside textbook scope; 0 false citations. |
| **C6** | Session Isolation | Simultaneous distinct sessions (Alice & Bob) | Lesson position, history, and state remain completely independent. |
| **R1** | Whole-Book Coverage | Inquiries on early (L1), mid (L9), late (L18) lessons | Chunks retrieved accurately from corresponding sections of `History.pdf`. |
| **R2** | Citation Integrity | Inspect attached citations on answers | Valid `pdf_page`, `book_page`, `lesson_title`; fully deduplicated. |
| **F1** | Adaptive Figure | Explore historical figure | Renders `FigureProfile` card with name, title, place, and teachings. |
| **F2** | Adaptive Comparison| Compare rulers in Lesson 1 | Renders `ComparisonData` grid (Akbar vs Sultans). |
| **F3** | Adaptive Timeline | Chronological sequence in Lesson 9 | Renders `TimelineEvent` step badges and descriptions. |
| **F4** | Adaptive Cause | Cause & effect in Lesson 2 / Lesson 9 | Renders 3-part card (Cause → Event → Lasting Significance). |
| **Q1** | Quiz Wrong Answer | Select incorrect option in challenge | Evaluated false; supportive clue displayed; retry offered. |
| **Q2** | Quiz Right Answer | Select correct option in challenge | Evaluated true; congratulations message; next lesson unlocked. |
| **VIS-1**| Browser UI | Full browser flow at `http://localhost:3000` | Header, avatars, illustration banners, choice buttons, composer verified. |
| **IMG-1**| Local Assets | Visual storytelling assets | 4 curated SVG illustrations + `manifest.json` load with 0 memory pressure. |
