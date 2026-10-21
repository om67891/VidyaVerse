"""
Curriculum Glossary Service & Tap-to-Reveal Engine.
Provides textbook-grounded definitions for key terminology in:
- History (Std IV Shivachhatrapati)
- Mathematics (Std X Part II)
- Environmental Studies (Std V How We Came to Be)
"""
from __future__ import annotations

import re
from typing import Optional
from pydantic import BaseModel, Field


class GlossaryTerm(BaseModel):
    term_id: str
    subject_id: str
    chapter_id: Optional[str] = None
    term: str
    definition: str
    detailed_definition: Optional[str] = None
    book_page: Optional[int] = None
    related_terms: list[str] = []


GLOSSARY_CATALOGUE: list[GlossaryTerm] = [
    # ── History Terms ─────────────────────────────────────────────────────────
    GlossaryTerm(
        term_id="HIST_SWARAJ",
        subject_id="history",
        chapter_id="HIST_L01",
        term="Swaraj",
        definition="Self-rule and independence for the people, establishing a just and righteous kingdom of their own.",
        detailed_definition="Shivaji Maharaj founded Swaraj in Maharashtra so that people of all faiths, castes, and backgrounds could live with dignity, freedom, and protection.",
        book_page=1,
        related_terms=["Chhatrapati", "Raireshwar"],
    ),
    GlossaryTerm(
        term_id="HIST_CHHATRAPATI",
        subject_id="history",
        chapter_id="HIST_L15",
        term="Chhatrapati",
        definition="The sovereign ruler and protector of the people holding the golden umbrella of royal authority.",
        detailed_definition="Conferred upon Shivaji Maharaj at his grand formal coronation on Raigad Fort on 6 June 1674, marking the formal recognition of Maratha sovereignty.",
        book_page=57,
        related_terms=["Swaraj", "Coronation", "Raigad"],
    ),
    GlossaryTerm(
        term_id="HIST_GHANIMIKAVA",
        subject_id="history",
        chapter_id="HIST_L07",
        term="Ghanimikava",
        definition="Guerrilla warfare tactics using speed, local geography, mountain valleys, and surprise.",
        detailed_definition="A military strategy perfected by Maratha soldiers who used the rugged Sahyadri terrain to defeat much larger imperial armies through swift surprise maneuvers.",
        book_page=26,
        related_terms=["Mavalas", "Sahyadri"],
    ),
    GlossaryTerm(
        term_id="HIST_WATANDAR",
        subject_id="history",
        chapter_id="HIST_L01",
        term="Watandar",
        definition="Feudal landholders and jagirdars in Maharashtra who controlled territories and collected taxes.",
        detailed_definition="Before Shivaji Maharaj, local Watandars constantly fought among themselves, causing immense hardship and devastation to the common people.",
        book_page=2,
        related_terms=["Deshmukh", "Deshpande"],
    ),
    GlossaryTerm(
        term_id="HIST_ABHANGA",
        subject_id="history",
        chapter_id="HIST_L02",
        term="Abhanga",
        definition="Devotional poetic verses sung by Maharashtra's saints praising God and teaching moral life.",
        detailed_definition="Famous abhangas composed by Sant Dnyaneshwar, Sant Namdeo, Sant Eknath, and Sant Tukaram brought spiritual wisdom in simple Marathi directly to the common folk.",
        book_page=4,
        related_terms=["Bhakti", "Tukaram Gatha"],
    ),
    GlossaryTerm(
        term_id="HIST_BHAVARTHA_DEEPIKA",
        subject_id="history",
        chapter_id="HIST_L02",
        term="Bhavartha Deepika",
        definition="The famous Marathi philosophical commentary on the Bhagavad Gita written by Sant Dnyaneshwar.",
        detailed_definition="Commonly known as the Dnyaneshwari, written at Nevasa when Dnyaneshwar was only sixteen years old, making Sanskrit spiritual knowledge accessible in Prakrit Marathi.",
        book_page=4,
        related_terms=["Sant Dnyaneshwar", "Abhanga"],
    ),

    # ── Mathematics Terms ──────────────────────────────────────────────────────
    GlossaryTerm(
        term_id="MATH_HYPOTENUSE",
        subject_id="mathematics",
        chapter_id="mathematics_chapter_02",
        term="Hypotenuse",
        definition="The longest side of a right-angled triangle, directly opposite the 90° right angle.",
        detailed_definition="In triangle ABC with angle B = 90°, side AC is the hypotenuse. By Pythagoras Theorem: AC^2 = AB^2 + BC^2.",
        book_page=30,
        related_terms=["Pythagoras Theorem", "Pythagorean Triplet"],
    ),
    GlossaryTerm(
        term_id="MATH_PYTHAGOREAN_TRIPLET",
        subject_id="mathematics",
        chapter_id="mathematics_chapter_02",
        term="Pythagorean Triplet",
        definition="A set of three natural numbers (a, b, c) where the square of the largest equals the sum of squares of the other two.",
        detailed_definition="Examples include (3, 4, 5) because 3^2 + 4^2 = 9 + 16 = 25 = 5^2, and (5, 12, 13), (8, 15, 17), (7, 24, 25).",
        book_page=30,
        related_terms=["Hypotenuse", "Pythagoras Theorem"],
    ),
    GlossaryTerm(
        term_id="MATH_SIMILAR_TRIANGLES",
        subject_id="mathematics",
        chapter_id="mathematics_chapter_01",
        term="Similar Triangles",
        definition="Two triangles having equal corresponding angles and proportional corresponding sides.",
        detailed_definition="Denoted by symbol '~'. If triangle ABC ~ triangle PQR, then AB/PQ = BC/QR = AC/PR and angle A = angle P, angle B = angle Q, angle C = angle R.",
        book_page=1,
        related_terms=["AAA test", "SAS test", "Basic Proportionality Theorem"],
    ),
    GlossaryTerm(
        term_id="MATH_TANGENT",
        subject_id="mathematics",
        chapter_id="mathematics_chapter_03",
        term="Tangent",
        definition="A straight line that touches a circle at exactly one point, perpendicular to the radius at that point.",
        detailed_definition="The point where the line touches is called the point of contact. The Tangent Theorem states that the radius to the point of contact is perpendicular to the tangent.",
        book_page=51,
        related_terms=["Secant", "Point of contact", "Chord"],
    ),
    GlossaryTerm(
        term_id="MATH_CYCLIC_QUADRILATERAL",
        subject_id="mathematics",
        chapter_id="mathematics_chapter_03",
        term="Cyclic Quadrilateral",
        definition="A quadrilateral whose all four vertices lie on the circumference of a single circle.",
        detailed_definition="The Cyclic Quadrilateral Theorem proves that opposite angles of a cyclic quadrilateral are supplementary: angle A + angle C = 180° and angle B + angle D = 180°.",
        book_page=68,
        related_terms=["Inscribed angle", "Circle"],
    ),
    GlossaryTerm(
        term_id="MATH_ANGLE_OF_ELEVATION",
        subject_id="mathematics",
        chapter_id="mathematics_chapter_06",
        term="Angle of Elevation",
        definition="The angle between the horizontal line of sight and the observer's line of sight directed upward toward an object.",
        detailed_definition="When looking up at the top of a tree, building, or tower from the ground, the angle measured above the horizontal line is the angle of elevation.",
        book_page=132,
        related_terms=["Angle of depression", "Line of sight", "Trigonometry"],
    ),
    GlossaryTerm(
        term_id="MATH_SECTOR",
        subject_id="mathematics",
        chapter_id="mathematics_chapter_07",
        term="Sector of a Circle",
        definition="The portion of a circle enclosed by two radii and the arc between them.",
        detailed_definition="The area of a sector with central angle theta (in degrees) is given by A = (theta / 360) * pi * r^2. Length of arc is L = (theta / 360) * 2 * pi * r.",
        book_page=151,
        related_terms=["Arc length", "Central angle", "Mensuration"],
    ),

    # ── EVS Terms ─────────────────────────────────────────────────────────────
    GlossaryTerm(
        term_id="EVS_EVOLUTION",
        subject_id="evs",
        chapter_id="EVS_CH04",
        term="Evolution",
        definition="The process of gradual and continuous change in living organisms over millions of years.",
        detailed_definition="Organisms that adapt to environmental changes survive and reproduce, while traits that help survival are passed on to subsequent generations.",
        book_page=15,
        related_terms=["Natural selection", "Charles Darwin", "Adaptation"],
    ),
    GlossaryTerm(
        term_id="EVS_HOMO_HABILIS",
        subject_id="evs",
        chapter_id="EVS_CH05",
        term="Homo habilis",
        definition="'The skilled human' who was the first species of human to make stone tools.",
        detailed_definition="Lived approximately 2 million years ago in Africa; fossil remains found in Olduvai Gorge in Tanzania. Made crude Oldowan pebble choppers.",
        book_page=20,
        related_terms=["Oldowan", "Stone tools", "Homo erectus"],
    ),
    GlossaryTerm(
        term_id="EVS_HOMO_ERECTUS",
        subject_id="evs",
        chapter_id="EVS_CH05",
        term="Homo erectus",
        definition="'The human who walked erect', mastering upright posture, coordinated hunting, and fire.",
        detailed_definition="Developed Acheulean handaxes with symmetrical edges and balance, and spread across Africa, Europe, and Asia.",
        book_page=21,
        related_terms=["Acheulean", "Handaxe", "Homo habilis"],
    ),
    GlossaryTerm(
        term_id="EVS_MICROLITHS",
        subject_id="evs",
        chapter_id="EVS_CH06",
        term="Microliths",
        definition="Small, sharp geometric stone blades made during the Middle Stone Age (Mesolithic).",
        detailed_definition="Fitted into wooden or bone grooves with tree resin to create composite hunting weapons like spears, arrows, and harvesting sickles.",
        book_page=28,
        related_terms=["Mesolithic", "Stone Age", "Handaxe"],
    ),
    GlossaryTerm(
        term_id="EVS_STRATIGRAPHY",
        subject_id="evs",
        chapter_id="EVS_CH02",
        term="Stratigraphy",
        definition="The archaeological study of rock and soil layers (strata) to date historical remains.",
        detailed_definition="Deeper archaeological strata are older than the upper strata, allowing scientists to determine the chronological sequence of human settlements.",
        book_page=7,
        related_terms=["Carbon-14 dating", "Archaeology"],
    ),
]


class GlossaryService:
    def get_terms_for_chapter(
        self,
        subject_id: str,
        chapter_id: Optional[str] = None,
    ) -> list[GlossaryTerm]:
        norm_sub = (subject_id or "").strip().lower()
        if norm_sub in ("math", "maths"):
            norm_sub = "mathematics"

        results = []
        for t in GLOSSARY_CATALOGUE:
            if t.subject_id.lower() != norm_sub:
                continue
            if chapter_id and t.chapter_id:
                # Normalize chapter numbers
                cur_m = re.search(r"(\d+)", chapter_id)
                t_m = re.search(r"(\d+)", t.chapter_id)
                if cur_m and t_m and cur_m.group(1) == t_m.group(1):
                    results.append(t)
                elif t.chapter_id.lower() == chapter_id.lower():
                    results.append(t)
            else:
                results.append(t)
        return results

    def get_term_by_name(self, term_name: str, subject_id: Optional[str] = None) -> Optional[GlossaryTerm]:
        clean = term_name.strip().lower()
        norm_sub = subject_id.strip().lower() if subject_id else None
        if norm_sub in ("math", "maths"):
            norm_sub = "mathematics"

        for t in GLOSSARY_CATALOGUE:
            if norm_sub and t.subject_id.lower() != norm_sub:
                continue
            if t.term.lower() == clean or clean in [r.lower() for r in t.related_terms]:
                return t
        return None

    def detect_terms_in_text(self, text: str, subject_id: str) -> list[GlossaryTerm]:
        """Detect any registered glossary terms appearing in answer text for frontend tap-to-reveal."""
        norm_sub = (subject_id or "").strip().lower()
        if norm_sub in ("math", "maths"):
            norm_sub = "mathematics"

        detected: list[GlossaryTerm] = []
        seen = set()

        for t in GLOSSARY_CATALOGUE:
            if t.subject_id.lower() != norm_sub:
                continue
            # Look for whole word match
            pattern = rf"\b{re.escape(t.term)}\b"
            if re.search(pattern, text, re.IGNORECASE) and t.term_id not in seen:
                detected.append(t)
                seen.add(t.term_id)

        return detected


_glossary_service: Optional[GlossaryService] = None


def get_glossary_service() -> GlossaryService:
    global _glossary_service
    if _glossary_service is None:
        _glossary_service = GlossaryService()
    return _glossary_service
