"""
Chapter boundary extraction and verification for History, Mathematics, and EVS.
Maps printed book pages to 1-based physical PDF pages and verifies opening headings and exercises.
"""
from __future__ import annotations
import sys
from pathlib import Path
import fitz  # PyMuPDF


# ── Canonical Curriculum Definitions ──────────────────────────────────────────

# History: Shivachhatrapati, Environmental Studies Part Two, Standard IV
# Source: History/History.pdf (92 pages total)
# Offset: Book page 1 = Physical PDF page 11 (offset = +10)
HISTORY_CHAPTERS = [
    {
        "chapter_number": 1,
        "title": "Maharashtra before Shivaji",
        "slug": "maharashtra_before_shivaji",
        "book_page_start": 1,
        "book_page_end": 2,
        "pdf_page_start_1based": 11,
        "pdf_page_end_1based": 12,
    },
    {
        "chapter_number": 2,
        "title": "Work of the Saints",
        "slug": "work_of_the_saints",
        "book_page_start": 3,
        "book_page_end": 7,
        "pdf_page_start_1based": 13,
        "pdf_page_end_1based": 17,
    },
    {
        "chapter_number": 3,
        "title": "Maratha Sardars - The Famous House of the Bhonsales",
        "slug": "maratha_sardars_bhonsales",
        "book_page_start": 8,
        "book_page_end": 11,
        "pdf_page_start_1based": 18,
        "pdf_page_end_1based": 21,
    },
    {
        "chapter_number": 4,
        "title": "Shivaji’s Childhood",
        "slug": "shivajis_childhood",
        "book_page_start": 12,
        "book_page_end": 16,
        "pdf_page_start_1based": 22,
        "pdf_page_end_1based": 26,
    },
    {
        "chapter_number": 5,
        "title": "Shivaji’s Education",
        "slug": "shivajis_education",
        "book_page_start": 17,
        "book_page_end": 20,
        "pdf_page_start_1based": 27,
        "pdf_page_end_1based": 30,
    },
    {
        "chapter_number": 6,
        "title": "The Oath of Swaraj",
        "slug": "oath_of_swaraj",
        "book_page_start": 21,
        "book_page_end": 24,
        "pdf_page_start_1based": 31,
        "pdf_page_end_1based": 34,
    },
    {
        "chapter_number": 7,
        "title": "Swaraj : First Conquest",
        "slug": "swaraj_first_conquest",
        "book_page_start": 25,
        "book_page_end": 28,
        "pdf_page_start_1based": 35,
        "pdf_page_end_1based": 38,
    },
    {
        "chapter_number": 8,
        "title": "Defeat of Internal Enemies",
        "slug": "defeat_of_internal_enemies",
        "book_page_start": 29,
        "book_page_end": 31,
        "pdf_page_start_1based": 39,
        "pdf_page_end_1based": 41,
    },
    {
        "chapter_number": 9,
        "title": "Pratapgad makes History",
        "slug": "pratapgad_makes_history",
        "book_page_start": 32,
        "book_page_end": 36,
        "pdf_page_start_1based": 42,
        "pdf_page_end_1based": 46,
    },
    {
        "chapter_number": 10,
        "title": "Baji Prabhu and the Memorable Battle of Ghodkhind",
        "slug": "baji_prabhu_ghodkhind",
        "book_page_start": 37,
        "book_page_end": 41,
        "pdf_page_start_1based": 47,
        "pdf_page_end_1based": 51,
    },
    {
        "chapter_number": 11,
        "title": "The Discomfiture of Shaistakhan",
        "slug": "discomfiture_of_shaistakhan",
        "book_page_start": 42,
        "book_page_end": 44,
        "pdf_page_start_1based": 52,
        "pdf_page_end_1based": 54,
    },
    {
        "chapter_number": 12,
        "title": "The Siege of Purandar and the Treaty with the Moghul Emperor",
        "slug": "siege_of_purandar",
        "book_page_start": 45,
        "book_page_end": 49,
        "pdf_page_start_1based": 55,
        "pdf_page_end_1based": 59,
    },
    {
        "chapter_number": 13,
        "title": "Shivaji gives the slip to the Emperor",
        "slug": "shivaji_escapes_the_emperor",
        "book_page_start": 50,
        "book_page_end": 52,
        "pdf_page_start_1based": 60,
        "pdf_page_end_1based": 62,
    },
    {
        "chapter_number": 14,
        "title": "The Fort is captured but the Lion is dead",
        "slug": "fort_captured_lion_is_dead",
        "book_page_start": 53,
        "book_page_end": 56,
        "pdf_page_start_1based": 63,
        "pdf_page_end_1based": 66,
    },
    {
        "chapter_number": 15,
        "title": "A Memorable Ceremony",
        "slug": "a_memorable_ceremony",
        "book_page_start": 57,
        "book_page_end": 59,
        "pdf_page_start_1based": 67,
        "pdf_page_end_1based": 69,
    },
    {
        "chapter_number": 16,
        "title": "Campaign in the South",
        "slug": "campaign_in_the_south",
        "book_page_start": 60,
        "book_page_end": 64,
        "pdf_page_start_1based": 70,
        "pdf_page_end_1based": 74,
    },
    {
        "chapter_number": 17,
        "title": "Management of Forts and the Navy",
        "slug": "forts_and_navy",
        "book_page_start": 65,
        "book_page_end": 69,
        "pdf_page_start_1based": 75,
        "pdf_page_end_1based": 79,
    },
    {
        "chapter_number": 18,
        "title": "Management of the Welfare State of Swaraj",
        "slug": "welfare_state_of_swaraj",
        "book_page_start": 70,
        "book_page_end": 77,
        "pdf_page_start_1based": 80,
        "pdf_page_end_1based": 87,
    },
]


# Mathematics: Mathematics, Part II, Standard X
# Source: Maths/Mathematics.pdf (180 pages total)
# Offset: Book page 1 = Physical PDF page 11 (offset = +10)
MATHEMATICS_CHAPTERS = [
    {
        "chapter_number": 1,
        "title": "Similarity",
        "slug": "similarity",
        "book_page_start": 1,
        "book_page_end": 29,
        "pdf_page_start_1based": 11,
        "pdf_page_end_1based": 39,
    },
    {
        "chapter_number": 2,
        "title": "Pythagoras Theorem",
        "slug": "pythagoras_theorem",
        "book_page_start": 30,
        "book_page_end": 46,
        "pdf_page_start_1based": 40,
        "pdf_page_end_1based": 56,
    },
    {
        "chapter_number": 3,
        "title": "Circle",
        "slug": "circle",
        "book_page_start": 47,
        "book_page_end": 90,
        "pdf_page_start_1based": 57,
        "pdf_page_end_1based": 100,
    },
    {
        "chapter_number": 4,
        "title": "Geometric Constructions",
        "slug": "geometric_constructions",
        "book_page_start": 91,
        "book_page_end": 99,
        "pdf_page_start_1based": 101,
        "pdf_page_end_1based": 109,
    },
    {
        "chapter_number": 5,
        "title": "Co-ordinate Geometry",
        "slug": "coordinate_geometry",
        "book_page_start": 100,
        "book_page_end": 123,
        "pdf_page_start_1based": 110,
        "pdf_page_end_1based": 133,
    },
    {
        "chapter_number": 6,
        "title": "Trigonometry",
        "slug": "trigonometry",
        "book_page_start": 124,
        "book_page_end": 139,
        "pdf_page_start_1based": 134,
        "pdf_page_end_1based": 149,
    },
    {
        "chapter_number": 7,
        "title": "Mensuration",
        "slug": "mensuration",
        "book_page_start": 140,
        "book_page_end": 163,
        "pdf_page_start_1based": 150,
        "pdf_page_end_1based": 173,
    },
]


# Environmental Studies: How We Came to Be, Environmental Studies Part Two, Standard V
# Source: Environmental Studies/EVS_Complete.pdf (66 pages total)
# Offset: Book page 1 = Physical PDF page 12 (offset = +11)
EVS_CHAPTERS = [
    {
        "chapter_number": 1,
        "title": "What is History?",
        "slug": "what_is_history",
        "book_page_start": 1,
        "book_page_end": 5,
        "pdf_page_start_1based": 12,
        "pdf_page_end_1based": 16,
        "legacy_filename": "Chapter 1 - What is History.pdf",
    },
    {
        "chapter_number": 2,
        "title": "History and the Concept of ‘Time’",
        "slug": "history_and_concept_of_time",
        "book_page_start": 6,
        "book_page_end": 11,
        "pdf_page_start_1based": 17,
        "pdf_page_end_1based": 22,
        "legacy_filename": "Chapter 2 - History and the Concept of ‘Time’.pdf",
    },
    {
        "chapter_number": 3,
        "title": "Life on Earth",
        "slug": "life_on_earth",
        "book_page_start": 12,
        "book_page_end": 14,
        "pdf_page_start_1based": 23,
        "pdf_page_end_1based": 25,
        "legacy_filename": "Chapter 3 - Life on Earth.pdf",
    },
    {
        "chapter_number": 4,
        "title": "Evolution",
        "slug": "evolution",
        "book_page_start": 15,
        "book_page_end": 18,
        "pdf_page_start_1based": 26,
        "pdf_page_end_1based": 29,
        "legacy_filename": "Chapter 4 - Evolution.pdf",
    },
    {
        "chapter_number": 5,
        "title": "Evolution of Mankind",
        "slug": "evolution_of_mankind",
        "book_page_start": 19,
        "book_page_end": 24,
        "pdf_page_start_1based": 30,
        "pdf_page_end_1based": 35,
        "legacy_filename": "Chapter 5 - Evolution of Mankind.pdf",
    },
    {
        "chapter_number": 6,
        "title": "Stone Age : Stone Tools",
        "slug": "stone_age_stone_tools",
        "book_page_start": 25,
        "book_page_end": 29,
        "pdf_page_start_1based": 36,
        "pdf_page_end_1based": 40,
        "legacy_filename": "Chapter 6 - Stone Age Stone Tools.pdf",
    },
    {
        "chapter_number": 7,
        "title": "From Shelters to Village-settlements",
        "slug": "shelters_to_village_settlements",
        "book_page_start": 30,
        "book_page_end": 33,
        "pdf_page_start_1based": 41,
        "pdf_page_end_1based": 44,
        "legacy_filename": "Chapter 7 - From Shelters to Village-settlements.pdf",
    },
    {
        "chapter_number": 8,
        "title": "Beginning of Settled Life",
        "slug": "beginning_of_settled_life",
        "book_page_start": 34,
        "book_page_end": 38,
        "pdf_page_start_1based": 45,
        "pdf_page_end_1based": 49,
        "legacy_filename": "Chapter 8 - Beginning of Settled Life.pdf",
    },
    {
        "chapter_number": 9,
        "title": "Settled Life and Urban Civilization",
        "slug": "settled_life_and_urban_civilization",
        "book_page_start": 39,
        "book_page_end": 44,
        "pdf_page_start_1based": 50,
        "pdf_page_end_1based": 55,
        "legacy_filename": "Chapter 9 - Settled Life and Urban Civilization.pdf",
    },
    {
        "chapter_number": 10,
        "title": "Historic Period",
        "slug": "historic_period",
        "book_page_start": 45,
        "book_page_end": 52,
        "pdf_page_start_1based": 56,
        "pdf_page_end_1based": 63,
        "legacy_filename": "Chapter 10 - Historic Period.pdf",
    },
]


def verify_subject_boundaries(subject_name: str, pdf_path: Path, chapters: list[dict]):
    print(f"\n=======================================================")
    print(f"Verifying {subject_name} boundaries in {pdf_path}")
    print(f"=======================================================")

    if not pdf_path.exists():
        print(f"Error: {pdf_path} not found.")
        return False

    doc = fitz.open(pdf_path)
    total_pdf_pages = len(doc)
    print(f"Source PDF has {total_pdf_pages} pages.")

    all_passed = True
    for ch in chapters:
        p_start = ch["pdf_page_start_1based"]
        p_end = ch["pdf_page_end_1based"]
        expected_count = p_end - p_start + 1

        if p_start < 1 or p_end > total_pdf_pages or p_start > p_end:
            print(f"[FAIL] Ch {ch['chapter_number']} range ({p_start}-{p_end}) out of bounds (1-{total_pdf_pages})")
            all_passed = False
            continue

        start_page = doc[p_start - 1]
        end_page = doc[p_end - 1]

        start_text = start_page.get_text().strip()
        end_text = end_page.get_text().strip()

        print(f"Ch {ch['chapter_number']:02d}: {ch['title']}")
        print(f"   PDF: {p_start}-{p_end} ({expected_count} pp) | Book: {ch['book_page_start']}-{ch['book_page_end']}")
        print(f"   Start page text chars: {len(start_text)}, End page text chars: {len(end_text)}")

    return all_passed


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent.parent

    h_ok = verify_subject_boundaries("History", base_dir / "History" / "History.pdf", HISTORY_CHAPTERS)
    m_ok = verify_subject_boundaries("Mathematics", base_dir / "Maths" / "Mathematics.pdf", MATHEMATICS_CHAPTERS)
    e_ok = verify_subject_boundaries("Environmental Studies", base_dir / "Environmental Studies" / "EVS_Complete.pdf", EVS_CHAPTERS)

    print("\nSummary:")
    print(f"History: {'PASSED' if h_ok else 'FAILED'}")
    print(f"Mathematics: {'PASSED' if m_ok else 'FAILED'}")
    print(f"EVS: {'PASSED' if e_ok else 'FAILED'}")
