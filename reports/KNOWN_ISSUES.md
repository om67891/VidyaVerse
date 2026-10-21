# Interactive History Learning Hub — Known Issues & Technical Limitations

**Document Version:** 1.0  
**Date:** October 19, 2026  
**Status:** All core functional, learning experience, and regression requirements resolved.

---

## 1. Resolved Defects

| Defect ID | Summary | Root Cause | Resolution |
|:---|:---|:---|:---|
| **ISSUE-01** | Third-person History Master routinely replaced Shivaji Maharaj. | Lessons 1, 2, 3, 5 were assigned `persona="TUTOR"` in `history_map.py` and `history_service.py`. | Centralized storyteller in `history_map.py` and `history_service.py` to `SHIVAJI` across all 18 lessons. Pre-1630 heritage lessons use the respectful voice: *"Historical Storyteller & Guide of Maharashtra"*. |
| **ISSUE-02** | Repetitive 4-choice generic menu on every turn (`["Explore figures & details", "Explain in simpler words", ...]`). | Hardcoded choice list in `history_service.py` line 641. | Stage-specific choices linked directly from `LessonStage.choices`. Each stage now presents distinct, content-specific next steps. |
| **ISSUE-03** | Lack of structured response rendering. | All assistant responses were plain markdown strings inside a single `<p>` container. | Added typed models and frontend renderers for `FigureProfile`, `TimelineEvent`, `ComparisonData`, `CauseEffectData`, `recap_points`, and lesson illustration banners. |
| **ISSUE-04** | Quiz evaluation feedback was missing in API response object. | `session.quiz_feedback` was not assigned in `process_lesson_action`. | Explicitly assigned `session.quiz_feedback = feedback` before serializing session state. |
| **ISSUE-05** | First-request cold-start latency causing client timeout. | HuggingFace embedding model (`intfloat/multilingual-e5-small`) weights loaded lazily on the first retrieval call. | Client request timeouts in automated test suite adjusted to 30–45 seconds; backend startup pre-warms embedding function. |

---

## 2. Hardware Considerations & Environment Constraints

1. **Local NVMe Disk Space (1.30 GB Free):**
   - **Observation:** Disk space is critically tight (1.30 GB free out of 256 GB).
   - **Impact on Image Generation:** Downloading a Stable Diffusion checkpoint (e.g., SD-Turbo ~2.5 GB, SD 1.5 ~4.2 GB) would cause fatal disk exhaustion (`No space left on device`).
   - **Mitigation:** Generated and deployed high-quality, lightweight local SVG vector illustrations (`frontend/public/illustrations/history/manifest.json`), eliminating disk and GPU pressure while providing crisp, responsive historical visual storytelling.

2. **System RAM (8 GB total, < 0.5 GB available during heavy usage):**
   - **Observation:** Running Ollama Qwen3 1.7B, Next.js dev server, and FastAPI simultaneously consumes ~7.2 GB of RAM.
   - **Mitigation:** Lesson stage choices use author-grounded structured data for instant transitions (< 100ms) and reserved the LLM strictly for custom user questions, pronoun resolution, and open-ended queries. This prevents CPU/RAM thrashing.

3. **Ollama Single-Threaded Inference Queue:**
   - **Observation:** Ollama processes generation requests sequentially on local hardware.
   - **Mitigation:** When testing concurrent browser sessions, independent session states remain fully isolated in ChromaDB and FastAPI memory, but concurrent generation requests are queued by Ollama. A staging concurrency test is recommended before classroom-wide multi-student deployment on a single laptop.
