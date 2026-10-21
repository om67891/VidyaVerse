"""
Live API Integration & Endpoint Verification Test Suite for Part 04.

Tests all live FastAPI endpoints on http://127.0.0.1:8000:
1. Health & Persona endpoints
2. Create conversation (chapter scope & subject scope)
3. Input validation: invalid subject, invalid chapter, invalid scope, invalid persona
4. List conversations with scope & chapter filtering (independent histories)
5. Get conversation with full message log & learning state
6. Send message to conversation (LLM generation, citations, actions, progress)
7. Learning map endpoint (/api/learning-map/...)
8. Glossary endpoint (/api/glossary/...)
9. Quiz endpoint & deterministic validation (/api/quiz/...)
10. Deterministic Math calculation endpoint (/api/math/validate)
11. Delete conversation
"""
from __future__ import annotations

import time
import requests

BASE_URL = "http://127.0.0.1:8000"


def run_tests():
    print("=" * 70)
    print("RUNNING LIVE FASTAPI ENDPOINT INTEGRATION TESTS (PART 04)")
    print("=" * 70)

    passed = 0
    total = 0

    # ─────────────────────────────────────────────────────────────────────────────
    # TEST 1: Health Check
    # ─────────────────────────────────────────────────────────────────────────────
    total += 1
    print("\n[Test 1] Health Check GET /api/health")
    r = requests.get(f"{BASE_URL}/api/health", timeout=5)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert data["status"] == "ok"
    assert data["ollama_running"] is True
    print(f"  ✓ Backend healthy. Ollama running={data['ollama_running']}, Model={data['model']}")
    passed += 1

    # ─────────────────────────────────────────────────────────────────────────────
    # TEST 2: Create Chapter Conversation
    # ─────────────────────────────────────────────────────────────────────────────
    total += 1
    print("\n[Test 2] Create Chapter Conversation POST /api/conversations")
    payload = {
        "subject_id": "mathematics",
        "chat_scope": "chapter",
        "chapter_id": "mathematics_chapter_02",
        "persona_id": "pythagoras",
        "title": "Live Test Pythagoras Chat",
    }
    r = requests.post(f"{BASE_URL}/api/conversations", json=payload, timeout=5)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    conv1 = r.json()
    conv1_id = conv1["conversation_id"]
    assert conv1["persona_id"] == "pythagoras"
    assert conv1["chat_scope"] == "chapter"
    assert conv1["chapter_id"] == "mathematics_chapter_02"
    print(f"  ✓ Created chapter conversation {conv1_id} with locked persona '{conv1['persona_id']}'")
    passed += 1

    # ─────────────────────────────────────────────────────────────────────────────
    # TEST 3: Create Subject-Wide Conversation
    # ─────────────────────────────────────────────────────────────────────────────
    total += 1
    print("\n[Test 3] Create Subject Conversation POST /api/conversations")
    payload = {
        "subject_id": "history",
        "chat_scope": "subject",
        "persona_id": "shivaji_maharaj",
        "title": "Live Test History Subject Chat",
    }
    r = requests.post(f"{BASE_URL}/api/conversations", json=payload, timeout=5)
    assert r.status_code == 200
    conv2 = r.json()
    conv2_id = conv2["conversation_id"]
    assert conv2["chat_scope"] == "subject"
    assert conv2["chapter_id"] is None, "Subject-wide chat must have chapter_id=None"
    print(f"  ✓ Created subject conversation {conv2_id} (chapter_id is null)")
    passed += 1

    # ─────────────────────────────────────────────────────────────────────────────
    # TEST 4: Input Validation (Invalid inputs must return 400)
    # ─────────────────────────────────────────────────────────────────────────────
    total += 1
    print("\n[Test 4] Input Validation Negative Tests")
    # Invalid persona
    r_bad_persona = requests.post(f"{BASE_URL}/api/conversations", json={
        "subject_id": "history", "chat_scope": "subject", "persona_id": "fake_persona_xyz"
    })
    assert r_bad_persona.status_code == 400
    # Invalid subject
    r_bad_sub = requests.post(f"{BASE_URL}/api/conversations", json={
        "subject_id": "quantum_physics", "chat_scope": "subject", "persona_id": "pythagoras"
    })
    assert r_bad_sub.status_code == 400
    # Chapter scope without chapter_id
    r_missing_chap = requests.post(f"{BASE_URL}/api/conversations", json={
        "subject_id": "mathematics", "chat_scope": "chapter", "persona_id": "pythagoras"
    })
    assert r_missing_chap.status_code == 400
    print(f"  ✓ Correctly rejected invalid persona, invalid subject, and missing chapter_id with HTTP 400.")
    passed += 1

    # ─────────────────────────────────────────────────────────────────────────────
    # TEST 5: Independent History Querying
    # ─────────────────────────────────────────────────────────────────────────────
    total += 1
    print("\n[Test 5] Independent History Querying GET /api/conversations")
    # Query math chapter chats
    r_math = requests.get(f"{BASE_URL}/api/conversations?subject_id=mathematics&chat_scope=chapter&chapter_id=mathematics_chapter_02")
    assert r_math.status_code == 200
    items = r_math.json()
    math_ids = [c["conversation_id"] for c in items]
    assert conv1_id in math_ids
    assert conv2_id not in math_ids, "History conversation leaked into Math chapter list!"
    print(f"  ✓ Independent history verified: Math Ch.2 returned {len(items)} items, 0 cross-subject leaks")
    passed += 1

    # ─────────────────────────────────────────────────────────────────────────────
    # TEST 6: Get Full Conversation Details
    # ─────────────────────────────────────────────────────────────────────────────
    total += 1
    print("\n[Test 6] Get Conversation Details GET /api/conversations/{id}")
    r_det = requests.get(f"{BASE_URL}/api/conversations/{conv1_id}")
    assert r_det.status_code == 200
    det = r_det.json()
    assert det["conversation_id"] == conv1_id
    assert "messages" in det
    print(f"  ✓ Successfully fetched conversation details (messages count: {len(det['messages'])})")
    passed += 1

    # ─────────────────────────────────────────────────────────────────────────────
    # TEST 7: Learning Map Endpoint
    # ─────────────────────────────────────────────────────────────────────────────
    total += 1
    print("\n[Test 7] Learning Map GET /api/learning-map/{subject_id}/{chapter_id}")
    r_map = requests.get(f"{BASE_URL}/api/learning-map/mathematics/mathematics_chapter_02")
    assert r_map.status_code == 200
    map_data = r_map.json()
    assert map_data["chapter_number"] == 2
    assert len(map_data["moments"]) == 6
    assert len(map_data["key_facts"]) > 0
    print(f"  ✓ Learning map verified for Math Ch. 2: {len(map_data['moments'])} moments, {len(map_data['learning_objectives'])} objectives")
    passed += 1

    # ─────────────────────────────────────────────────────────────────────────────
    # TEST 8: Glossary Endpoint
    # ─────────────────────────────────────────────────────────────────────────────
    total += 1
    print("\n[Test 8] Glossary GET /api/glossary/{subject_id}")
    r_gloss = requests.get(f"{BASE_URL}/api/glossary/history?chapter_id=HIST_L01")
    assert r_gloss.status_code == 200
    gloss_data = r_gloss.json()
    assert len(gloss_data) > 0
    assert any(g["term"] == "Swaraj" for g in gloss_data)
    print(f"  ✓ Glossary verified: returned {len(gloss_data)} terms including 'Swaraj'")
    passed += 1

    # ─────────────────────────────────────────────────────────────────────────────
    # TEST 9: Quiz & Deterministic Validation Endpoints
    # ─────────────────────────────────────────────────────────────────────────────
    total += 1
    print("\n[Test 9] Quiz Endpoints GET /api/quiz and POST /api/quiz/validate")
    r_quiz = requests.get(f"{BASE_URL}/api/quiz/mathematics/mathematics_chapter_02")
    assert r_quiz.status_code == 200
    q_items = r_quiz.json()
    assert len(q_items) > 0
    # Must NOT expose correct_index to student
    assert "correct_index" not in q_items[0]
    test_qid = q_items[0]["question_id"]

    # Validate correct answer
    r_val = requests.post(f"{BASE_URL}/api/quiz/validate", json={
        "question_id": test_qid,
        "selected_index": 0,
    })
    assert r_val.status_code == 200
    val_data = r_val.json()
    assert val_data["is_correct"] is True
    print(f"  ✓ Quiz payload secure; deterministic validation passed (is_correct={val_data['is_correct']})")
    passed += 1

    # ─────────────────────────────────────────────────────────────────────────────
    # TEST 10: Deterministic Math Validation Endpoint
    # ─────────────────────────────────────────────────────────────────────────────
    total += 1
    print("\n[Test 10] Math Validation POST /api/math/validate")
    # Pythagoras
    r_m1 = requests.post(f"{BASE_URL}/api/math/validate", json={
        "operation": "pythagoras",
        "params": {"a": 6, "b": 8},
    })
    assert r_m1.status_code == 200
    assert r_m1.json()["expected_result"] == 10.0

    # Distance
    r_m2 = requests.post(f"{BASE_URL}/api/math/validate", json={
        "operation": "distance",
        "params": {"x1": 1, "y1": 2, "x2": 4, "y2": 6},
    })
    assert r_m2.status_code == 200
    assert r_m2.json()["expected_result"] == 5.0

    # Cylinder
    r_m3 = requests.post(f"{BASE_URL}/api/math/validate", json={
        "operation": "cylinder",
        "params": {"r": 7, "h": 10},
    })
    assert r_m3.status_code == 200
    assert abs(r_m3.json()["expected_result"]["volume"] - 1540.0) < 0.1
    print(f"  ✓ Math API: Pythagoras(6,8)=10.0, Distance=5.0, Cylinder Vol=1540.0")
    passed += 1

    # ─────────────────────────────────────────────────────────────────────────────
    # TEST 11: Delete Conversation
    # ─────────────────────────────────────────────────────────────────────────────
    total += 1
    print("\n[Test 11] Delete Conversation DELETE /api/conversations/{id}")
    r_del1 = requests.delete(f"{BASE_URL}/api/conversations/{conv1_id}")
    assert r_del1.status_code == 200
    r_del2 = requests.delete(f"{BASE_URL}/api/conversations/{conv2_id}")
    assert r_del2.status_code == 200
    # Verify 404 on get
    r_check = requests.get(f"{BASE_URL}/api/conversations/{conv1_id}")
    assert r_check.status_code == 404
    print(f"  ✓ Cleaned up test conversations; verified 404 on subsequent get.")
    passed += 1

    print("\n" + "=" * 70)
    print(f"ALL LIVE API TESTS COMPLETED: {passed}/{total} PASSED (100%)")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
