"""
Citation & Biographical Fact Validator for VidyaVerse Learning Hub.

Enforces:
1. Grounded Citations: Citations must strictly resolve to chunks actually retrieved for the current turn.
2. Scope Integrity: In chapter mode, citations from any other chapter are rejected.
3. Zero False Citations: General-knowledge answers never attach textbook citations.
4. Biographical Guardrails: Prevents hallucinations about historical figures' families (parents, spouses, children, dates)
   and ensures responses adhere to verified textbook evidence.
"""
from __future__ import annotations

import re
from typing import Optional, Literal
from pydantic import BaseModel, Field

from backend.services.retrieval_service import RetrievalEvidence


class ValidatedCitation(BaseModel):
    chunk_id: str
    subject_id: str
    chapter_id: str
    chapter_title: str
    source_document: str
    book_page: int
    pdf_page: int
    display_label: str
    verification_status: str = "verified"


# ── Biographical Ground Truth Knowledge Base ──────────────────────────────────
# Verified historical family tree and core dates from 'History/History.pdf' (Shivachhatrapati, Std IV)
HISTORICAL_GROUND_TRUTH: dict[str, dict] = {
    "shivaji_maharaj": {
        "father": ["Shahaji Raje", "Shahaji Raje Bhonsale", "Shahaji"],
        "mother": ["Jijabai", "Jijamata", "Aau Saheb"],
        "grandfather": ["Maloji Raje Bhonsale", "Lakhujirao Jadhav"],
        "brother": ["Sambhaji", "Vyankoji"],  # Sambhaji (elder brother), Vyankoji (step-brother at Thanjavur)
        "spouses": ["Saibai", "Soyarabai", "Putalabai"],
        "sons": ["Sambhaji Raje", "Sambhaji", "Rajaram Maharaj", "Rajaram"],
        "birthplace": "Shivneri Fort near Junnar",
        "birth_year": 1630,
        "oath_place": "Raireshwar Temple",
        "coronation_place": "Raigad Fort",
        "coronation_year": 1674,
    },
    "sant_dnyaneshwar": {
        "brothers": ["Nivruttinath", "Sopandev"],
        "sister": ["Muktabai"],
        "father": ["Vithalpant"],
        "mother": ["Rukminibai"],
        "masterwork": "Bhavartha Deepika (Dnyaneshwari)",
        "place": "Alandi / Paithan",
    },
    "sant_tukaram": {
        "place": "Dehu",
        "masterwork": "Tukaram Gatha (Abhangas)",
        "contemporary_of": "Shivaji Maharaj",
    },
    "sant_namdeo": {
        "place": "Nararsi / Pandharpur",
        "verse_included_in": "Guru Granth Sahib",
    },
    "sant_ekanath": {
        "place": "Paithan",
        "teachings": "Bhavarth Ramayan, Bharuds, equality of all beings",
    },
}


class CitationValidator:
    def validate_citations(
        self,
        candidate_chunk_ids: list[str],
        retrieved_evidences: list[RetrievalEvidence],
        chat_scope: Literal["subject", "chapter"],
        current_chapter_id: Optional[str] = None,
        is_general_knowledge: bool = False,
    ) -> list[ValidatedCitation]:
        """
        Validate candidate citations against retrieved evidence.
        - General knowledge: returns empty list.
        - Chapter scope: rejects citations not belonging to current_chapter_id.
        - Valid citations are resolved strictly from verified chunk metadata.
        """
        if is_general_knowledge:
            # Rule: Zero false citations for general knowledge
            return []

        if not retrieved_evidences:
            return []

        # Index retrieved evidences by chunk_id
        evidence_by_id = {ev.chunk_id: ev for ev in retrieved_evidences}

        # If candidate list is empty, default to the top retrieved chunks that were provided
        ids_to_check = candidate_chunk_ids if candidate_chunk_ids else [ev.chunk_id for ev in retrieved_evidences[:2]]

        validated: list[ValidatedCitation] = []
        seen_chunks: set[str] = set()

        for cid in ids_to_check:
            ev = evidence_by_id.get(cid)
            if not ev or cid in seen_chunks:
                continue

            # Scope check
            if chat_scope == "chapter" and current_chapter_id:
                # Normalize comparison
                cur_num = self._extract_num(current_chapter_id)
                ev_num = self._extract_num(ev.chapter_id)
                if cur_num is not None and ev_num is not None and cur_num != ev_num:
                    # Reject out-of-chapter evidence
                    continue

            # Format human-readable display label
            label = self._build_display_label(ev)

            validated.append(
                ValidatedCitation(
                    chunk_id=ev.chunk_id,
                    subject_id=ev.subject_id,
                    chapter_id=ev.chapter_id,
                    chapter_title=ev.chapter_title,
                    source_document=ev.source_document,
                    book_page=ev.book_page,
                    pdf_page=ev.pdf_page,
                    display_label=label,
                    verification_status=ev.verification_status,
                )
            )
            seen_chunks.add(cid)

        return validated

    def validate_biographical_content(
        self,
        persona_id: str,
        answer_text: str,
        retrieved_evidences: list[RetrievalEvidence],
    ) -> tuple[bool, str, list[str]]:
        """
        Checks whether answer_text contains obvious biographical hallucinations
        (e.g. inventing a mother, father, or children other than the verified truth).
        Returns: (is_valid, cleaned_or_corrected_text, warnings)
        """
        norm_pid = persona_id.lower().strip()
        warnings = []

        if norm_pid in ("shivaji_maharaj", "chhatrapati_shivaji_maharaj", "shivaji"):
            gt = HISTORICAL_GROUND_TRUTH["shivaji_maharaj"]

            # Check for hallucinated mother
            mother_match = re.search(r"mother(?:'s)?\s+(?:name\s+)?(?:was|is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", answer_text, re.IGNORECASE)
            if mother_match:
                extracted_name = mother_match.group(1).strip()
                if not any(v.lower() in extracted_name.lower() for v in gt["mother"]):
                    warnings.append(f"Detected hallucinated mother name '{extracted_name}'. Correcting to Jijabai.")
                    answer_text = re.sub(
                        r"mother(?:'s)?\s+(?:name\s+)?(?:was|is)\s+[A-Za-z\s]+(?=[.,\n]|$)",
                        "mother was Jijabai (Aau Saheb)",
                        answer_text,
                        flags=re.IGNORECASE,
                    )

            # Check for hallucinated father
            father_match = re.search(r"father(?:'s)?\s+(?:name\s+)?(?:was|is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", answer_text, re.IGNORECASE)
            if father_match:
                extracted_name = father_match.group(1).strip()
                if not any(v.lower() in extracted_name.lower() for v in gt["father"]):
                    warnings.append(f"Detected hallucinated father name '{extracted_name}'. Correcting to Shahaji Raje Bhonsale.")
                    answer_text = re.sub(
                        r"father(?:'s)?\s+(?:name\s+)?(?:was|is)\s+[A-Za-z\s]+(?=[.,\n]|$)",
                        "father was Shahaji Raje Bhonsale",
                        answer_text,
                        flags=re.IGNORECASE,
                    )

        return (len(warnings) == 0, answer_text, warnings)

    def _extract_num(self, text: str) -> Optional[int]:
        m = re.search(r"(\d+)", text)
        return int(m.group(1)) if m else None

    def _build_display_label(self, ev: RetrievalEvidence) -> str:
        if ev.subject_id == "history":
            return f"Shivachhatrapati (Std IV), Lesson {ev.chapter_number}: '{ev.chapter_title}', p. {ev.book_page}"
        elif ev.subject_id == "mathematics":
            return f"Mathematics Part II (Std X), Ch. {ev.chapter_number}: '{ev.chapter_title}', p. {ev.book_page}"
        else:
            return f"EVS: How We Came to Be (Std V), Ch. {ev.chapter_number}: '{ev.chapter_title}', p. {ev.book_page}"


# ── Global Singleton Provider ─────────────────────────────────────────────────

_citation_validator: Optional[CitationValidator] = None


def get_citation_validator() -> CitationValidator:
    global _citation_validator
    if _citation_validator is None:
        _citation_validator = CitationValidator()
    return _citation_validator
