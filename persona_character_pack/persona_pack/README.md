# Persona Pack — Starter Profiles

This is a **character-definition pack only**. It does not modify, index, split, or otherwise change the learning-hub application or its PDFs.

## Directory structure

```text
personas/
  README.md
  catalog.json
  shared_behavior_contract.json
  persona_authoring_template.json
  history/*.json
  mathematics/*.json
  evs/*.json
```

## Starter catalogue (24 profiles)

### History — Standard IV *Shivachhatrapati*
- Chhatrapati Shivaji Maharaj
- Sant Dnyaneshwar
- Sant Namdeo
- Sant Eknath
- Sant Tukaram
- Samarth Ramdas
- Baji Prabhu Deshpande
- Moro Trimbak Pingle

### Mathematics — Standard X Part II
- Pythagoras
- Apollonius of Perga
- Similarity Coach
- Geometry Proof Coach
- Circle Geometry Coach
- Coordinate Geometry Coach
- Trigonometry Coach
- Mensuration Coach

The maths teaching roles are deliberately first-class options. The historical mathematicians are *inspired teaching personas*, not claims that those figures wrote this particular textbook or originated every syllabus concept.

### EVS — Standard V *How We Came to Be*
- Charles Darwin
- Carl Linnaeus
- Louis Leakey
- Christian Thomsen
- The Archaeologist
- The Human-Evolution Scientist
- The Prehistoric-Life Guide
- The Ancient-Civilization Guide

## Design principles

1. **Persona is more than a name/avatar.** Each file describes expertise, voice, behavioural traits, teaching style, response examples, and hard limits.
2. **Persona never beats evidence.** Retrieval, answer factuality, and citation validation are separate responsibilities.
3. **Do not fabricate first-person history.** Historical roleplay is clearly educational; it is not a transcript, diary, or authentic quotation.
4. **The persona stays locked per conversation.** Change persona by creating a new conversation, not by switching the narrator mid-chat.
5. **Two chat scopes.** Subject-wide chat may cover all chapters in one subject; chapter chat uses the selected chapter's retrieval boundary. Keep their histories separate.
6. **Outside-scope general knowledge.** Answer naturally where reliable but never add irrelevant textbook citations. Say when uncertain.
7. **Extend without rewrites.** Add a new JSON file and a catalog entry; use stable IDs in lowercase snake_case.
8. **Images are not included.** `avatar_key` is a logical asset name only. Use licensed or locally created artwork; do not assume an image exists.

## Textbook grounding status

Profiles mark themselves `starter_profile_needs_review` intentionally. They are sufficiently detailed to discuss and iterate on, but should not be treated as fully verified biographies. Chapter tags are routing guidance. At runtime, the correct PDF passages must still be retrieved and used to validate claims and displayed page citations.

## Runtime integration notes (future work; not implemented here)

- Load only valid profiles from this folder and reject duplicate `persona_id` values.
- Show the full subject catalogue in subject-wide persona selection.
- Filter or rank relevant personas for a chapter-specific picker; include a neutral tutor fallback where appropriate.
- Persist `persona_id`, `subject_id`, `chapter_id` (nullable), `chat_scope`, messages, timestamps, and lesson state per conversation.
- Construct the system prompt from `prompt.system_prompt` and the current session scope; append retrieved evidence separately.
- Do not let the language model create citation metadata; it must be sourced from retrieval results.
- Add automated tests for JSON schema, unique IDs, persona locking, role consistency, family-fact accuracy, out-of-scope handling, and citation relevance.

## Source files analysed

- `History.pdf`: Maharashtra State Board *Shivachhatrapati*, Environmental Studies Part II, Standard IV. The table of contents lists 18 lessons; the saints lesson names Dnyaneshwar, Namdeo, Eknath, Tukaram, Ramdas, and Chakradhar Swami; the welfare-state lesson lists Moro Trimbak Pingle as Pradhan.
- `Mathematics.pdf`: Maharashtra State Board Mathematics Part II, Standard X. The contents list Similarity, Pythagoras Theorem, Circle, Geometric Constructions, Co-ordinate Geometry, Trigonometry, and Mensuration. Apollonius theorem appears in the Pythagoras Theorem chapter.
- `EVS_Complete.pdf`: Maharashtra State Board *How We Came to Be*, Environmental Studies Part Two, Standard V. The contents list 10 history/evolution chapters. The text discusses Darwin, Linnaeus, Louis Leakey, and Christian Thomsen.

## External context used for careful character framing

- Sahitya Akademi biography on Dnyaneshwar: https://sahitya-akademi.gov.in/publications/pdf/p-y-deshpande_english.pdf
- Marathi Vishwakosh, Shivaji: https://vishwakosh.marathi.gov.in/33539/
- MacTutor, Pythagoras: https://mathshistory.st-andrews.ac.uk/Biographies/Pythagoras/
- MacTutor, Apollonius of Perga: https://mathshistory.st-andrews.ac.uk/Biographies/Apollonius/

External context should be clearly distinguished from textbook claims; it is not a replacement for the exact PDF evidence at answer time.
