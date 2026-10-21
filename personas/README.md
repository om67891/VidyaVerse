# VidyaVerse Persona Intelligence System

The VidyaVerse Persona Intelligence System provides a modular, offline-first educational character architecture across History, Mathematics, and Environmental Studies (EVS).

Each persona is an individually defined educational character with distinct identity, reasoning patterns, communication style, teaching methodology, source citations, and strict knowledge boundaries.

---

## 1. Directory Structure

```text
personas/
├── README.md                                 # This specification and runtime manual
├── schema/
│   ├── persona.schema.json                   # Authoritative Draft-07 JSON Schema
│   └── shared_behaviour_contract.json       # Core behavioral, factual, and interaction rules
│
├── history/
│   ├── index.json                            # History subject persona catalog
│   ├── shivaji_maharaj/
│   │   ├── profile.json                      # Authoritative profile definition
│   │   ├── sources.json                      # Textbook & secondary historical references
│   │   └── examples.jsonl                    # Validated few-shot educational interactions
│   ├── sant_dnyaneshwar/
│   ├── sant_namdeo/
│   ├── sant_ekanath/
│   ├── sant_tukaram/
│   ├── samarth_ramdas/
│   ├── baji_prabhu_deshpande/
│   └── moro_trimbak_pingle/
│
├── mathematics/
│   ├── index.json                            # Mathematics subject persona catalog
│   ├── pythagoras/
│   ├── apollonius/
│   ├── similarity_coach/
│   ├── geometry_proof_coach/
│   ├── circle_geometry_coach/
│   ├── coordinate_geometry_coach/
│   ├── trigonometry_coach/
│   └── mensuration_coach/
│
└── evs/
    ├── index.json                            # EVS subject persona catalog
    ├── charles_darwin/
    ├── carl_linnaeus/
    ├── louis_leakey/
    ├── christian_thomsen/
    ├── archaeologist/
    ├── human_evolution_scientist/
    ├── prehistoric_life_guide/
    └── ancient_civilization_guide/
```

---

## 2. Core Architectural Principles (Three Distinct Layers)

A persona is much more than a cosmetic tone or voice:

### Layer A — Knowledge & Evidence
- What is verified about the historical figure, scientist, or pedagogical domain.
- Grounded strictly in the official Maharashtra State Board textbook curriculum (History Std IV, Maths Std X, EVS Std V).
- Explicit boundaries distinguishing verified historical facts from unrecorded private thoughts or modern developments.

### Layer B — Reasoning & Teaching Methodology
- How the persona guides students toward deeper understanding:
  - **Shivaji Maharaj**: Strategic decision chains (Problem $\rightarrow$ Options $\rightarrow$ Decision $\rightarrow$ Consequence $\rightarrow$ Welfare).
  - **Saints of Maharashtra**: Compassion, egalitarian Bhakti traditions, everyday relatable reflections.
  - **Mathematicians & Coaches**: Structured proof steps, proportional reasoning, formula verification with units.
  - **Scientists & Guides**: Observation $\rightarrow$ Pattern $\rightarrow$ Scientific Hypothesis $\rightarrow$ Distinguishing physical artifacts from modern inferences.

### Layer C — Communication & Tone
- Distinct rhythm, sentence length, vocabulary tier, encouragement style, error handling, and question formats.

---

## 3. The 3 Response Modes

Every persona dynamically adapts to three clearly delineated response modes:

1. **`documented` (Textbook-Grounded)**:
   - Grounded strictly in the retrieved chapter passages from ChromaDB.
   - Genuine citations attached (`pdf_filename`, `page_number`).
   - If an unrecorded detail is asked, states limitation honestly without fabricating citations.
2. **`persona_inspired` (Pedagogical Modeling)**:
   - Explains concepts using the persona's characteristic reasoning framework without falsely claiming historical discovery of modern post-lifetime facts.
   - Preserves 100% modern mathematical and scientific accuracy.
3. **`imaginative` (Educational Roleplay)**:
   - Vivid educational scenes and narrative framing.
   - Visibly distinguishes dramatic storytelling from authentic historical evidence.
   - Never fabricates authentic quotations or unrecorded private conversations.

---

## 4. Question Format Mapping

The system matches the response structure to the pedagogical intent of the question:
- **Who?**: Structured portrait with role, period, documented deeds, and context.
- **Why?**: Cause-and-effect sequence or justified chain of reasoning.
- **How?**: Ordered sequential steps or a worked example.
- **When?**: Two-to-three event mini timeline or exact chronological order.
- **Compare**: Aligned comparison table or structured contrast points.
- **Solve**: Step-by-step mathematical derivation with intermediate substitutions and unit check.
- **Explain simply**: Concise explanation with one relatable analogy and comprehension check.
- **Story**: Sequence of structured story moments advancing the historical lesson.
- **Quiz**: Target question with validated answer choices.
- **Summarise**: 3-5 grounded key takeaways from the lesson.

---

## 5. Unique Visual Identities

Every persona features a **unique, purpose-designed SVG portrait** located in `frontend/public/avatars/{subject}/{persona_id}.svg`.
- Vector-crisp across all screen resolutions.
- 100% offline operation with zero HTTP dependencies.
- Distinct subject-appropriate fallback badges (History Saffron `#D97706`, Math Royal Blue `#2563EB`, EVS Emerald `#059669`).

---

## 6. How Profiles Are Loaded & Registered

The runtime service `backend.services.persona_manager.PersonaManager` loads profiles automatically on startup:
1. Discovers all subdirectories under `personas/{history,mathematics,evs}/`.
2. Validates `profile.json` against `personas/schema/persona.schema.json`.
3. Loads associated `sources.json` and `examples.jsonl`.
4. Exposes REST endpoints:
   - `GET /api/personas`: List all registered personas (filterable by `subject_id` and prioritized by `chapter_id`).
   - `GET /api/personas/{persona_id}`: Fetch full profile, boundaries, and sources.

---

## 7. How to Add a New Persona

1. Create a folder under the target subject: `personas/{subject}/{new_persona_id}/`.
2. Create `profile.json` following `personas/schema/persona.schema.json`.
3. Create `sources.json` mapping textbook lessons and secondary references.
4. Create `examples.jsonl` with at least 3 high-quality few-shot interactions.
5. Create an SVG portrait in `frontend/public/avatars/{subject}/{new_persona_id}.svg` and set `avatar_path`.
6. Add the entry to `personas/{subject}/index.json`.
7. Validate:
   ```bash
   .\.venv\Scripts\python.exe scripts/validate_personas.py
   ```

---

## 8. Validation & Evaluation

Run the validation and evaluation test suites:

```bash
# Validate schemas, sources, examples, and avatars
.\.venv\Scripts\python.exe scripts/validate_personas.py

# Run the 120-case evaluation suite (5 dimensions per persona)
.\.venv\Scripts\python.exe scripts/evaluate_personas.py

# Run prototype and RAG regression suites
.\.venv\Scripts\python.exe test_history_prototype.py
.\.venv\Scripts\python.exe test_poc.py
```
