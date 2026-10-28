"""
VidyaVerse Persona Manager Service:
Loads, validates, and manages the 24 educational personas from the authoritative personas/ directory.
Constructs dynamic, modular, source-grounded system prompts that blend:
  - Shared behavior contract (personas/schema/shared_behaviour_contract.json)
  - Persona profile (character voice, teaching identity, reasoning patterns, boundaries)
  - Active subject and chapter scope
  - Response mode ("documented" | "persona_inspired" | "imaginative")
  - Retrieved textbook evidence
  - Question format directives (Who, What, Why, How, When, Compare, Solve, Story, Quiz, Summarise)
  - Factual accuracy & anti-hallucination guardrails
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from backend.config import settings
from backend.schemas import PersonaSchema

PERSONAS_ROOT = Path(settings.subjects_base_path) / "personas"
CONTRACT_PATH = PERSONAS_ROOT / "schema" / "shared_behaviour_contract.json"

# Persona ID aliases to prevent breakage
PERSONA_ALIASES = {
    "sant_eknath": "sant_ekanath",
    "chhatrapati_shivaji_maharaj": "shivaji_maharaj",
    "shivaji": "shivaji_maharaj",
}


class PersonaManager:
    _instance: Optional[PersonaManager] = None

    def __init__(self):
        self.personas: dict[str, dict] = {}
        self.sources: dict[str, dict] = {}
        self.examples: dict[str, list[dict]] = {}
        self.contract: dict = {}
        self.load_catalogue()

    @classmethod
    def get_instance(cls) -> PersonaManager:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_catalogue(self) -> None:
        """Load all personas from personas/{history,mathematics,evs} directories."""
        self.personas.clear()
        self.sources.clear()
        self.examples.clear()

        # Load shared contract
        if CONTRACT_PATH.exists():
            try:
                self.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"[PersonaManager] Warning: Failed to load contract: {e}")
                self.contract = {}

        subjects = ["history", "mathematics", "evs"]
        for sub in subjects:
            sub_dir = PERSONAS_ROOT / sub
            if not sub_dir.exists():
                continue

            for p_dir in sub_dir.iterdir():
                if not p_dir.is_dir() or p_dir.name == "schema":
                    continue

                profile_path = p_dir / "profile.json"
                if not profile_path.exists():
                    continue

                try:
                    profile = json.loads(profile_path.read_text(encoding="utf-8"))
                    p_id = profile.get("persona_id")
                    if p_id:
                        self.personas[p_id] = profile

                        # Load sources
                        src_path = p_dir / profile.get("sources_file", "sources.json")
                        if src_path.exists():
                            self.sources[p_id] = json.loads(src_path.read_text(encoding="utf-8"))

                        # Load examples
                        ex_path = p_dir / profile.get("examples_file", "examples.jsonl")
                        if ex_path.exists():
                            lines = [l.strip() for l in ex_path.read_text(encoding="utf-8").splitlines() if l.strip()]
                            self.examples[p_id] = [json.loads(l) for l in lines]
                except Exception as e:
                    print(f"[PersonaManager] Error loading {profile_path}: {e}")

        print(f"[PersonaManager] Loaded {len(self.personas)} personas successfully.")

    def resolve_persona_id(self, persona_id: str) -> str:
        clean = (persona_id or "").strip().lower()
        return PERSONA_ALIASES.get(clean, clean)

    def get_persona(self, persona_id: str) -> Optional[dict]:
        clean_id = self.resolve_persona_id(persona_id)
        return self.personas.get(clean_id)

    def get_persona_schema(self, persona_id: str) -> Optional[PersonaSchema]:
        p = self.get_persona(persona_id)
        if not p:
            return None
        return PersonaSchema(
            persona_id=p["persona_id"],
            name=p["display_name"],
            subject_id=p["subject_id"],
            persona_type=p["persona_type"],
            card_summary=p["short_description"],
            primary_topics=p.get("expertise_topics", []),
            avatar_url=p.get("avatar_path"),
        )

    def list_personas(
        self,
        subject_id: Optional[str] = None,
        chapter_id: Optional[str] = None,
    ) -> list[PersonaSchema]:
        """
        List personas filtered by subject and prioritized by chapter relevance.
        """
        target_sub = subject_id.lower().strip() if subject_id else None
        if target_sub in ("math", "maths"):
            target_sub = "mathematics"

        results: list[dict] = []
        for p in self.personas.values():
            if not p.get("enabled", True):
                continue
            if target_sub and p.get("subject_id", "").lower() != target_sub:
                continue
            results.append(p)

        # Prioritize if chapter_id is given
        clean_chap = (chapter_id or "").strip().lower()

        def relevance_score(item: dict) -> tuple[int, str]:
            rel_chapters = [c.lower() for c in item.get("relevant_chapter_ids", [])]
            if clean_chap and (clean_chap in rel_chapters or any(clean_chap in c for c in rel_chapters)):
                return (0, item.get("display_name", ""))
            return (1, item.get("display_name", ""))

        if clean_chap:
            results.sort(key=relevance_score)

        return [
            PersonaSchema(
                persona_id=p["persona_id"],
                name=p["display_name"],
                subject_id=p["subject_id"],
                persona_type=p["persona_type"],
                card_summary=p["short_description"],
                primary_topics=p.get("expertise_topics", []),
                avatar_url=p.get("avatar_path"),
            )
            for p in results
        ]

    def build_system_prompt(
        self,
        persona_id: str,
        subject_name: str,
        chapter_name: Optional[str] = None,
        context_str: str = "",
        response_mode: str = "documented",
        question_format: Optional[str] = None,
    ) -> str:
        """
        Construct a dynamic, rich, and rigorous system prompt for local LLM inference.
        """
        p = self.get_persona(persona_id)
        if not p:
            # Fallback to standard tutor
            return (
                f"You are a helpful, factually precise educational tutor for {subject_name}.\n"
                f"Active Chapter: {chapter_name or 'General Subject'}\n"
                f"TEXTBOOK CONTEXT:\n{context_str}\n\n"
                "Answer the student's question directly, clearly, and concisely in clean Markdown."
            )

        name = p["display_name"]
        persona_type = p["persona_type"]
        comm = p.get("communication_style", {})
        teach = p.get("teaching_behaviour", {})
        boundaries = p.get("knowledge_boundaries", {})
        accuracy_rules = p.get("accuracy_rules", [])
        roleplay_rules = p.get("roleplay_rules", [])

        # Format directives mapping
        format_directive = ""
        format_map = self.contract.get("question_format_mapping", {})
        if question_format and question_format in format_map:
            format_directive = f"\nREQUIRED RESPONSE FORMAT ({question_format.upper()}):\n- {format_map[question_format]}\n"

        # Response mode guidance
        mode_instruction = ""
        if response_mode == "documented":
            mode_instruction = (
                "RESPONSE MODE: DOCUMENTED / TEXTBOOK-GROUNDED\n"
                "- When explaining lesson topics, ground your factual claims strictly in the verified textbook context provided.\n"
                "- When the student asks about your identity, family, background, parents, childhood, or personal journey, speak directly and warmly from your Core Documented Facts in the first person.\n"
                "- If a curriculum fact is missing from the context, state the limitation honestly without guessing.\n"
            )
        elif response_mode == "persona_inspired":
            mode_instruction = (
                "RESPONSE MODE: PERSONA-INSPIRED TEACHING\n"
                "- Teach the concept using your characteristic reasoning pattern, tone, and pedagogical style.\n"
                "- If explaining modern concepts, frame them through your perspective without falsely claiming historical discovery.\n"
                "- When asked about your identity or family, speak from your Core Documented Facts in the first person.\n"
            )
        elif response_mode == "imaginative":
            mode_instruction = (
                "RESPONSE MODE: IMAGINATIVE EDUCATIONAL ROLEPLAY\n"
                "- Use vivid storytelling to bring the scene to life.\n"
                "- Explicitly distinguish dramatic narrative from verified historical evidence.\n"
                "- Never present invented conversations as authentic historical quotes.\n"
            )

        # Assemble prompt sections
        prompt_parts = [
            f"You are {name}, an educational persona in the VidyaVerse Learning Hub.",
            f"Persona Role: {p.get('short_description')}",
            f"Subject: {subject_name} | Scope: {chapter_name or 'Entire Subject'}",
            f"Persona Type: {persona_type}",
            "",
            "=== CHARACTER VOICE & TEACHING METHOD ===",
            f"Tone: {comm.get('tone')}",
            f"Vocabulary Level: {comm.get('vocabulary_level')}",
            f"Explanation Structure: {comm.get('explanation_pattern')}",
            f"Teaching Method: {teach.get('student_interaction_style')}",
            f"Encouragement: {teach.get('encouragement_style')}",
            f"Handling Errors: {teach.get('misconception_handling')}",
            "",
            "=== REASONING PATTERNS ===",
            "\n".join(f"- {rp}" for rp in p.get("reasoning_patterns", [])),
            "",
            mode_instruction,
            format_directive,
            "=== CORE DOCUMENTED BIOGRAPHY & FACTS ===",
            "\n".join(f"- {df}" for df in p.get("documented_facts", [])),
            "- When the student asks about your identity, family, background, parents, childhood, or achievements, answer proudly, accurately, and warmly in the FIRST PERSON based on these facts. These are your authentic biographical truth.",
            "",
            "=== STRICT ACCURACY & KNOWLEDGE BOUNDARIES ===",
            "\n".join(f"- {ar}" for ar in accuracy_rules),
            "\n".join(f"- {rr}" for rr in roleplay_rules),
            f"- Verified Expertise: {', '.join(boundaries.get('verified_topics', []))}",
            f"- Limitations: {', '.join(boundaries.get('limited_topics', []))}",
            "- Universal Principle: Always answer the student's actual question first before adding story, reflection, or follow-ups.",
            "- Keep your response concise, engaging, and age-appropriate for a Class 5 student (typically 2 to 4 crisp sentences).",
            "- Do NOT prepend 'Student:' or 'Tutor:' or your own name at the beginning of the reply.",
            "- Do NOT append repetitive generic menus after every message.",
        ]

        if context_str:
            prompt_parts.extend([
                "",
                "=== TEXTBOOK CONTEXT (RETRIEVED PASSAGES) ===",
                context_str,
                "For lesson and curriculum questions, ground your answers in this textbook evidence. For personal identity and family questions, answer from your Core Documented Facts."
            ])

        return "\n".join(prompt_parts)


def get_persona_manager() -> PersonaManager:
    return PersonaManager.get_instance()
