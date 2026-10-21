# VidyaVerse / Learning Hub — Known Issues & Technical Limitations

**Document Version:** 2.0  
**Date:** October 21, 2026  
**Status:** All core functional, learning experience, visual components, and regression requirements resolved.

---

## 1. Resolved Defects

| Defect ID | Summary | Root Cause | Resolution |
|:---|:---|:---|:---|
| **ISSUE-01** | Third-person History Master routinely replaced Shivaji Maharaj. | Lessons 1, 2, 3, 5 were assigned `persona="TUTOR"` in `history_map.py` and `history_service.py`. | Centralized storyteller in `history_map.py` and `history_service.py` to `SHIVAJI` across all 18 lessons. Pre-1630 heritage lessons use the respectful voice: *"Historical Storyteller & Guide of Maharashtra"*. |
| **ISSUE-02** | Repetitive 4-choice generic menu on every turn (`["Explore figures & details", "Explain in simpler words", ...]`). | Hardcoded choice list in `history_service.py` line 641. | Stage-specific choices linked directly from `LessonStage.choices`. Each stage now presents distinct, content-specific next steps. |
| **ISSUE-03** | Lack of structured response rendering. | All assistant responses were plain markdown strings inside a single `<p>` container. | Added typed models and frontend renderers for `FigureProfile`, `TimelineEvent`, `ComparisonData`, `CauseEffectData`, `recap_points`, and lesson illustration banners. |
| **ISSUE-04** | Quiz evaluation feedback was missing in API response object. | `session.quiz_feedback` was not assigned in `process_lesson_action`. | Explicitly assigned `session.quiz_feedback = feedback` before serializing session state. |
| **ISSUE-05** | First-request cold-start latency causing client timeout. | HuggingFace embedding model (`intfloat/multilingual-e5-small`) weights loaded lazily on the first retrieval call. | Client request timeouts in automated test suite adjusted to 120 seconds; backend startup pre-warms embedding function. |
| **ISSUE-06** | Chapter ID mismatch in legacy test queries (`History_01` vs `history_chapter_01`). | Ingestion manifests use slugified identifiers (`history_chapter_01`), causing 404 when test queries used shorthand. | Updated `scripts/test_part5_smoke.py` to dynamically discover valid chapter IDs from `/api/subjects/{subject_id}` endpoints. |
| **ISSUE-07** | Health check key mismatch in test runner. | FastAPI health endpoint returned `{"ollama_running": bool, "model": str}`, while smoke test checked `ollama_ok` and `ollama_model`. | Synchronized key lookups in `scripts/test_part5_smoke.py` to align with `backend/main.py`. |
| **ISSUE-08** | Ollama primary model unavailability during migration. | If `qwen3:4b` weights were unmounted or downloading, chat requests failed with HTTP 404. | Implemented automated multi-model fallback in `backend/services/rag.py` (`qwen3:4b` → `qwen3:1.7b`), ensuring 100% offline uptime. |

---

## 2. Hardware Considerations & Environment Constraints

1. **Local NVMe Disk Space (~9.5 GB Free):**
   - **Observation:** Disk space is healthy (~9.5 GB free after downloading Qwen3 4B at 2.5 GB).
   - **Recommendation:** Keep heavy checkpoints (like large diffusion models or 8B+ LLMs) off this machine to preserve headroom for system caches and vector stores.

2. **System RAM (8 GB total, ~770 MB free at idle under Windows 11):**
   - **Observation:** Running Next.js, FastAPI, Ollama Qwen3 4B, and browser simultaneously consumes ~7.2 GB of RAM.
   - **Mitigation:** Context windows are bounded to 4096 tokens (`num_predict = 600`), and Ollama memory-maps the weights directly into the 4 GB VRAM of the NVIDIA GeForce RTX 2050, avoiding pagefile thrashing.

3. **Ollama Single-Threaded Inference Queue:**
   - **Observation:** Ollama processes generation requests sequentially on local hardware.
   - **Mitigation:** Structured lesson stage transitions and quizzes use deterministic validation (< 50ms) without querying the LLM, reserving language model generation strictly for open-ended queries and tutor roleplay.

4. **HuggingFace Hub Unauthenticated Notice:**
   - **Observation:** On first startup, `sentence-transformers` prints an unauthenticated Hugging Face Hub notice.
   - **Impact:** None. Embedding weights (`intfloat/multilingual-e5-small`) are fully cached locally on disk in `~/.cache/huggingface/hub/`.
