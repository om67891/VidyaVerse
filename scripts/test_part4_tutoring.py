"""
Comprehensive Tutoring, Math Validation, Glossary, and Quiz Tests for Part 04.

Tests:
1. MathValidator: Deterministic evaluations for Pythagoras, 30-60-90, Apollonius, Co-ordinate Geometry, Trigonometry, and Mensuration.
2. LearningMapService: Curriculum moments and honest progress tracking.
3. GlossaryService: Chapter-specific terms and text detection for tap-to-reveal.
4. QuizService: Secure student-facing payloads and deterministic grading.
5. CitationValidator: Biographical guardrails and zero false citations for general knowledge.
6. TutoringService: Full pipeline processing with intent routing, persona prompts, and state updates.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.math_validator import get_math_validator
from backend.services.learning_map_service import get_learning_map_service
from backend.services.glossary_service import get_glossary_service
from backend.services.quiz_service import get_quiz_service
from backend.services.citation_validator import get_citation_validator
from backend.services.tutoring_service import get_tutoring_service, TutoringMessageRequest
from backend.repositories.conversation_repository import get_conversation_repository


def run_tests():
    print("=" * 70)
    print("RUNNING TUTORING, MATH VALIDATION, GLOSSARY & QUIZ TESTS (PART 04)")
    print("=" * 70)

    passed = 0
    total = 0

    mv = get_math_validator()
    lms = get_learning_map_service()
    gs = get_glossary_service()
    qs = get_quiz_service()
    cv = get_citation_validator()
    repo = get_conversation_repository()
    ts = get_tutoring_service()

    # ─────────────────────────────────────────────────────────────────────────────
    # TEST 1: Deterministic Math - Pythagoras & Triplets
    # ─────────────────────────────────────────────────────────────────────────────
    total += 1
    print("\n[Test 1] Deterministic Pythagoras Calculations")
    res = mv.solve_pythagoras(a=3, b=4)
    assert res.is_valid and res.expected_result == 5.0, f"Expected 5.0, got {res.expected_result}"
    res_leg = mv.solve_pythagoras(c=13, a=5)
    assert res_leg.is_valid and res_leg.expected_result == 12.0
    res_trip = mv.solve_pythagoras(a=8, b=15, c=17)
    assert res_trip.is_valid and res_trip.expected_result is True
    res_notrip = mv.solve_pythagoras(a=4, b=5, c=6)
    assert res_notrip.expected_result is False
    print(f"  ✓ Validated hypotenuse(3,4)=5.0, leg(13,5)=12.0, triplet(8,15,17)=True, triplet(4,5,6)=False")
    passed += 1

    # ─────────────────────────────────────────────────────────────────────────────
    # TEST 2: Deterministic Math - 30-60-90 & Apollonius
    # ─────────────────────────────────────────────────────────────────────────────
    total += 1
    print("\n[Test 2] Deterministic 30-60-90 & Apollonius Theorem")
    res_30 = mv.solve_30_60_90(hypotenuse=10.0)
    assert res_30.expected_result["side_30"] == 5.0
    assert abs(res_30.expected_result["side_60"] - 8.6603) < 0.01

    res_apol = mv.solve_apollonius(ab=10.0, ac=12.0, bm=6.0)
    assert res_apol.is_valid and res_apol.expected_result is not None
    print(f"  ✓ 30-60-90 hypotenuse 10: side_30=5.0, side_60=8.6603; Apollonius median AM={res_apol.expected_result}")
    passed += 1

    # ─────────────────────────────────────────────────────────────────────────────
    # TEST 3: Deterministic Math - Co-ordinate Geometry & Trigonometry
    # ─────────────────────────────────────────────────────────────────────────────
    total += 1
    print("\n[Test 3] Deterministic Co-ordinate Geometry & Trigonometry")
    d_res = mv.coordinate_distance(0, 0, 3, 4)
    assert d_res.expected_result == 5.0
    m_res = mv.coordinate_slope(1, 2, 3, 6)
    assert m_res.expected_result == 2.0
    sin_res = mv.trig_standard_value("sin", 30)
    assert sin_res.expected_result == "1/2"
    tan_res = mv.trig_standard_value("tan", 45)
    assert tan_res.expected_result == "1"
    print(f"  ✓ Distance((0,0),(3,4))=5.0, Slope((1,2),(3,6))=2.0, sin(30°)=1/2, tan(45°)=1")
    passed += 1

    # ─────────────────────────────────────────────────────────────────────────────
    # TEST 4: Deterministic Math - Mensuration (Cylinder & Cone)
    # ─────────────────────────────────────────────────────────────────────────────
    total += 1
    print("\n[Test 4] Deterministic Mensuration (Cylinder & Cone)")
    cyl = mv.mensuration_cylinder(r=7, h=10)
    assert abs(cyl.expected_result["volume"] - 1540.0) < 0.1
    cone = mv.mensuration_cone(r=3, h=4)
    assert cone.expected_result["slant_height"] == 5.0
    print(f"  ✓ Cylinder r=7,h=10: Volume={cyl.expected_result['volume']}; Cone r=3,h=4: Slant height={cone.expected_result['slant_height']}")
    passed += 1

    # ─────────────────────────────────────────────────────────────────────────────
    # TEST 5: Learning Map & Moments Explored Progress
    # ─────────────────────────────────────────────────────────────────────────────
    total += 1
    print("\n[Test 5] Learning Map & Progress Calculation")
    m_map = lms.get_chapter_map("mathematics", "mathematics_chapter_02")
    assert m_map is not None
    assert len(m_map.moments) == 6
    assert m_map.moments[0].moment_id == "MATH_CH02_M01"

    # Compute progress with 2 moments explored
    prog = lms.compute_progress("mathematics", "mathematics_chapter_02", ["MATH_CH02_M01", "MATH_CH02_M02"])
    assert prog["total_moments"] == 6
    assert prog["explored_count"] == 2
    assert prog["percentage"] == 33.3
    assert "You've explored 2 of 6 learning moments" in prog["display_text"]
    assert prog["next_moment"]["moment_id"] == "MATH_CH02_M03"
    print(f"  ✓ {prog['display_text']}, Next moment: {prog['next_moment']['title']}")
    passed += 1

    # ─────────────────────────────────────────────────────────────────────────────
    # TEST 6: Glossary Tap-to-Reveal Engine
    # ─────────────────────────────────────────────────────────────────────────────
    total += 1
    print("\n[Test 6] Glossary Retrieval & Text Detection")
    terms = gs.get_terms_for_chapter("history", "HIST_L01")
    assert any(t.term == "Swaraj" for t in terms)

    math_terms = gs.get_terms_for_chapter("mathematics", "mathematics_chapter_02")
    assert any(t.term == "Hypotenuse" for t in math_terms)

    # Detect in sample tutor text
    sample_text = "In right triangle ABC, the hypotenuse is opposite the right angle, and Chhatrapati Shivaji fought for Swaraj."
    detected_hist = gs.detect_terms_in_text(sample_text, "history")
    detected_math = gs.detect_terms_in_text(sample_text, "mathematics")
    assert any(t.term == "Swaraj" for t in detected_hist)
    assert any(t.term == "Hypotenuse" for t in detected_math)
    print(f"  ✓ Detected glossary terms: History={[t.term for t in detected_hist]}, Math={[t.term for t in detected_math]}")
    passed += 1

    # ─────────────────────────────────────────────────────────────────────────────
    # TEST 7: Quiz Generation & Deterministic Validation
    # ─────────────────────────────────────────────────────────────────────────────
    total += 1
    print("\n[Test 7] Quiz Payload Security & Grading")
    q_list = qs.get_questions_for_chapter("mathematics", "mathematics_chapter_02")
    assert len(q_list) > 0
    # Must NOT have correct_index attribute exposed
    assert not hasattr(q_list[0], "correct_index")
    qid = q_list[0].question_id

    # Validate correct answer (index 0)
    res_correct = qs.validate_answer(qid, 0)
    assert res_correct.is_correct is True
    # Validate wrong answer (index 1)
    res_wrong = qs.validate_answer(qid, 1)
    assert res_wrong.is_correct is False
    assert "Not quite" in res_wrong.feedback
    print(f"  ✓ Secured quiz payload (correct_index hidden); graded answer deterministic (Correct={res_correct.is_correct}, Wrong={res_wrong.is_correct})")
    passed += 1

    # ─────────────────────────────────────────────────────────────────────────────
    # TEST 8: Biographical Guardrails & Zero False Citations
    # ─────────────────────────────────────────────────────────────────────────────
    total += 1
    print("\n[Test 8] Biographical Guardrails & Citation Rules")
    # General knowledge -> zero citations
    cits_gk = cv.validate_citations([], [], "chapter", "HIST_L01", is_general_knowledge=True)
    assert len(cits_gk) == 0, "General knowledge MUST have 0 citations!"

    # Biographical check: test if hallucinated mother is caught and corrected
    test_hallucinated = "My mother was Putalabai and she taught me warfare."
    valid, corrected, warnings = cv.validate_biographical_content("shivaji_maharaj", test_hallucinated, [])
    assert "Jijabai" in corrected, f"Failed to correct hallucinated mother: {corrected}"
    print(f"  ✓ Zero false citations verified. Biographical hallucination corrected to: '{corrected}'")
    passed += 1

    # ─────────────────────────────────────────────────────────────────────────────
    # TEST 9: Full Tutoring Pipeline Integration (General Knowledge vs Chapter)
    # ─────────────────────────────────────────────────────────────────────────────
    total += 1
    print("\n[Test 9] Full Tutoring Pipeline: General Knowledge query during Chapter Chat")
    test_conv = repo.create_conversation(
        subject_id="history",
        chat_scope="chapter",
        chapter_id="HIST_L02",
        persona_id="shivaji_maharaj",
        title="Testing GK in Chapter Mode",
    )
    t_id = test_conv["conversation_id"]

    # Student asks general science question in History chapter
    resp = ts.process_message(
        TutoringMessageRequest(
            conversation_id=t_id,
            message="What is photosynthesis in simple terms?",
        )
    )
    assert resp.response_mode == "general_knowledge"
    assert len(resp.citations) == 0, "GK question during History chat must NEVER attach History citations!"
    assert len(resp.suggested_actions) > 0
    print(f"  ✓ Mode={resp.response_mode}, Citations={len(resp.citations)}, Actions={len(resp.suggested_actions)}")
    passed += 1

    # ─────────────────────────────────────────────────────────────────────────────
    # TEST 10: Interruption & Return-to-Lesson Action Preservation
    # ─────────────────────────────────────────────────────────────────────────────
    total += 1
    print("\n[Test 10] Interruption & Return-to-Lesson Action Preservation")
    # Simulate an active moment suspended by a custom question
    repo.update_learning_state(t_id, {
        "explored_moment_ids": ["HIST_L02_S1_INTRO"],
        "current_moment_id": "HIST_L02_S2_DNYANESHWAR",
        "suspended_moment_id": "HIST_L02_S2_DNYANESHWAR",
    })
    resp_interrupted = ts.process_message(
        TutoringMessageRequest(
            conversation_id=t_id,
            message="Can you explain this word to me?",
        )
    )
    # The first suggested action must offer to return to the lesson
    action_types = [a.action_type for a in resp_interrupted.suggested_actions]
    assert "resume_lesson" in action_types, f"Expected resume_lesson in actions, got {action_types}"
    print(f"  ✓ Return-to-lesson action preserved: {[a.label for a in resp_interrupted.suggested_actions if a.action_type == 'resume_lesson'][0]}")
    passed += 1

    # Clean up test conversation
    repo.delete_conversation(t_id)

    print("\n" + "=" * 70)
    print(f"TUTORING & VALIDATION TESTS COMPLETED: {passed}/{total} PASSED (100%)")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
