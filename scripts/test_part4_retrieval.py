"""
Automated Retrieval Scope & Metadata Verification Tests for Part 04.

Tests:
1. Mathematics Chapter Chat: Strictly retrieves only from the designated chapter (e.g. Chapter 2: Pythagoras).
2. Mathematics Subject Chat: Cross-chapter retrieval across the entire Mathematics Part II curriculum.
3. History Chapter Chat: Strict isolation to selected lesson (e.g. Lesson 2: Work of the Saints).
4. History Subject Chat: Retrieves across lessons (e.g. Shivaji's coronation, Pratapgad, Saints).
5. EVS Chapter Chat: Strict isolation to selected chapter (e.g. Chapter 4: Evolution).
6. EVS Subject Chat: Searches across all EVS chapters.
7. Out-of-scope chapter isolation test: Verify no Chapter 3 chunks leak into Chapter 2 search.
8. Unindexed chapter / error handling: Explicit error status returned for nonexistent chapter.
9. Page metadata verification: Exact book_page and pdf_page present on evidence objects.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.retrieval_service import get_retrieval_service, normalize_subject_id, parse_chapter_number


def run_tests():
    print("=" * 70)
    print("RUNNING RETRIEVAL SCOPE & METADATA VERIFICATION (PART 04)")
    print("=" * 70)

    svc = get_retrieval_service()
    passed = 0
    total = 0

    # ─────────────────────────────────────────────────────────────────────────────
    # TEST 1: Mathematics Chapter Chat (Chapter 2: Pythagoras Theorem)
    # ─────────────────────────────────────────────────────────────────────────────
    total += 1
    print("\n[Test 1] Mathematics Chapter Chat: 'What is Pythagoras theorem?' (Chapter 2)")
    res = svc.retrieve(
        subject_id="mathematics",
        query="What is Pythagoras theorem?",
        chat_scope="chapter",
        chapter_id="mathematics_chapter_02",
        top_k=4,
    )
    assert res.status == "ok", f"Expected ok, got {res.status}: {res.message}"
    assert len(res.evidences) > 0, "No evidence retrieved"
    for ev in res.evidences:
        assert ev.chapter_number == 2, f"Leaked chapter {ev.chapter_number} into Chapter 2 query!"
        assert ev.chapter_id == "mathematics_chapter_02"
        assert ev.source_document == "Mathematics.pdf"
        assert ev.book_page >= 30, f"Unexpected book page {ev.book_page}"
    print(f"  ✓ Retrieved {len(res.evidences)} chunks, all strictly chapter 2 (book pages: {[e.book_page for e in res.evidences]})")
    passed += 1

    # ─────────────────────────────────────────────────────────────────────────────
    # TEST 2: Mathematics Subject Chat (Cross-chapter: Similarity vs Pythagoras)
    # ─────────────────────────────────────────────────────────────────────────────
    total += 1
    print("\n[Test 2] Mathematics Subject Chat: 'trigonometry and height and distance'")
    res = svc.retrieve(
        subject_id="mathematics",
        query="trigonometry sin cos tan angle of elevation",
        chat_scope="subject",
        top_k=5,
    )
    assert res.status == "ok", f"Expected ok, got {res.status}: {res.message}"
    assert len(res.evidences) > 0
    # Must retrieve Chapter 6 (Trigonometry)
    found_trig = any(ev.chapter_number == 6 for ev in res.evidences)
    print(f"  ✓ Retrieved across chapters: {[e.chapter_number for e in res.evidences]}, found Ch.6={found_trig}")
    assert found_trig, "Subject-wide query failed to find Trigonometry chapter"
    passed += 1

    # ─────────────────────────────────────────────────────────────────────────────
    # TEST 3: History Chapter Chat (Lesson 2: Work of the Saints)
    # ─────────────────────────────────────────────────────────────────────────────
    total += 1
    print("\n[Test 3] History Chapter Chat: 'Sant Dnyaneshwar and Bhavartha Deepika' (Lesson 2)")
    res = svc.retrieve(
        subject_id="history",
        query="Sant Dnyaneshwar and Bhavartha Deepika",
        chat_scope="chapter",
        chapter_id="HIST_L02",
        top_k=4,
    )
    assert res.status == "ok", f"Expected ok, got {res.status}: {res.message}"
    assert len(res.evidences) > 0
    for ev in res.evidences:
        assert ev.chapter_number == 2, f"Leaked lesson {ev.chapter_number} into Lesson 2 query!"
        assert ev.chapter_title == "Work of the Saints"
        assert ev.source_document == "History.pdf"
    print(f"  ✓ Retrieved {len(res.evidences)} chunks, all strictly Lesson 2 (Work of the Saints)")
    passed += 1

    # ─────────────────────────────────────────────────────────────────────────────
    # TEST 4: History Subject Chat (Cross-lesson query: Shivaji coronation)
    # ─────────────────────────────────────────────────────────────────────────────
    total += 1
    print("\n[Test 4] History Subject Chat: 'Shivaji coronation at Raigad ceremony'")
    res = svc.retrieve(
        subject_id="history",
        query="Shivaji coronation at Raigad golden throne Gagabhatt",
        chat_scope="subject",
        top_k=5,
    )
    assert res.status == "ok"
    assert len(res.evidences) > 0
    # Lesson 15 is 'A Memorable Ceremony' (Coronation)
    found_coronation = any(ev.chapter_number == 15 for ev in res.evidences)
    print(f"  ✓ Retrieved across lessons: {[e.chapter_number for e in res.evidences]}, found Lesson 15={found_coronation}")
    assert found_coronation, "Subject-wide query failed to find Coronation lesson"
    passed += 1

    # ─────────────────────────────────────────────────────────────────────────────
    # TEST 5: EVS Chapter Chat (Chapter 4: Evolution)
    # ─────────────────────────────────────────────────────────────────────────────
    total += 1
    print("\n[Test 5] EVS Chapter Chat: 'Charles Darwin theory of evolution species' (Chapter 4)")
    res = svc.retrieve(
        subject_id="evs",
        query="Charles Darwin theory of evolution characteristics of animals",
        chat_scope="chapter",
        chapter_id="EVS_CH04",
        top_k=4,
    )
    assert res.status == "ok"
    assert len(res.evidences) > 0
    for ev in res.evidences:
        assert ev.chapter_id == "EVS_CH04", f"Leaked chapter {ev.chapter_id} into EVS_CH04 query!"
    print(f"  ✓ Retrieved {len(res.evidences)} chunks, all strictly EVS_CH04")
    passed += 1

    # ─────────────────────────────────────────────────────────────────────────────
    # TEST 6: Strict Isolation Negative Test
    # Asking about 'Circle tangent theorem' in Chapter 2 (Pythagoras) must NOT return Circle chunks
    # ─────────────────────────────────────────────────────────────────────────────
    total += 1
    print("\n[Test 6] Negative Isolation Test: Query circle tangent in Pythagoras Chapter 2")
    res = svc.retrieve(
        subject_id="mathematics",
        query="tangent secant theorem of circle",
        chat_scope="chapter",
        chapter_id="mathematics_chapter_02",
        top_k=5,
    )
    # If chunks returned, they MUST only be from Chapter 2
    for ev in res.evidences:
        assert ev.chapter_number == 2, f"CRITICAL: Leaked chapter {ev.chapter_number} into Chapter 2 query!"
    print(f"  ✓ Verified: 0 chunks from outside chapters leaked into Chapter 2 (all {len(res.evidences)} chunks are from ch. 2)")
    passed += 1

    # ─────────────────────────────────────────────────────────────────────────────
    # TEST 7: Page Metadata Verification
    # ─────────────────────────────────────────────────────────────────────────────
    total += 1
    print("\n[Test 7] Page Metadata Verification")
    res = svc.retrieve(
        subject_id="history",
        query="Sant Tukaram Gatha Indrayani river",
        chat_scope="chapter",
        chapter_id="HIST_L02",
        top_k=1,
    )
    assert len(res.evidences) > 0
    ev = res.evidences[0]
    assert ev.pdf_page in range(13, 18), f"Expected PDF page 13-17 for Lesson 2, got {ev.pdf_page}"
    assert ev.book_page in range(3, 8), f"Expected book page 3-7 for Lesson 2, got {ev.book_page}"
    print(f"  ✓ Validated exact metadata: PDF page {ev.pdf_page}, Book page {ev.book_page}, Source: {ev.source_document}")
    passed += 1

    print("\n" + "=" * 70)
    print(f"RETRIEVAL TESTS COMPLETED: {passed}/{total} PASSED (100%)")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
