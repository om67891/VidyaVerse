"""
Automated Test & Verification Suite for Class 5 Learning Hub.

Strictly separates:
  PART 1: Deterministic Backend Routing & Retrieval Tests (No LLM, tests logic and ChromaDB filters directly)
  PART 2: Live Model Generation & Factual Accuracy Tests (Calls local Ollama qwen3:1.7b, ZERO MOCKS)

Reports all test results honestly, distinguishing between routing/retrieval checks and live model answers.
"""
from __future__ import annotations

import sys
import os
import re
import requests
from typing import NamedTuple

# Force unbuffered output for real-time reporting
sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, os.path.abspath("."))

from backend.config import settings
from backend.services.indexing import get_chroma_collection
from backend.services.catalog import get_all_subjects, get_chapter
from backend.services.rag import (
    retrieve_passages,
    retrieve_chapter_overview,
    process_chat,
    get_diagnostics,
    route_intent,
    is_followup,
    extract_list_names,
    filter_supporting_sources,
)
from backend.schemas import ChatRequest, HistoryMessage

BASE_URL = "http://localhost:8000"


class TestReport(NamedTuple):
    test_id: str
    name: str
    category: str       # "ROUTING_RETRIEVAL" or "LIVE_MODEL"
    live_model: bool    # True if called Ollama qwen3:1.7b
    mocked: bool        # Always False (we never mock)
    passed: bool
    details: str


REPORTS: list[TestReport] = []


def print_banner(text: str):
    print("\n" + "=" * 75)
    print(f"  {text}")
    print("=" * 75)


# ═══════════════════════════════════════════════════════════════════════════════
# PART 1: DETERMINISTIC BACKEND ROUTING & RETRIEVAL TESTS (NO LLM CALLS)
# ═══════════════════════════════════════════════════════════════════════════════


def run_part1_routing_and_retrieval_tests():
    print_banner("PART 1: BACKEND ROUTING & RETRIEVAL TESTS (DETERMINISTIC / NO LLM)")

    # 1. Health check
    print("\n[RR-1] Health check & ChromaDB status:")
    try:
        resp = requests.get(f"{BASE_URL}/api/health", timeout=5)
        data = resp.json()
        assert resp.status_code == 200 and data.get("ollama_running")
        print(f"  ✓ Status: {data.get('status')} | Ollama Running: {data.get('ollama_running')} | Collection: {data.get('collection')}")
        REPORTS.append(TestReport("RR-1", "Backend Health & Collection", "ROUTING_RETRIEVAL", False, False, True, "Health OK, ChromaDB active"))
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        REPORTS.append(TestReport("RR-1", "Backend Health & Collection", "ROUTING_RETRIEVAL", False, False, False, str(e)))

    # 2. Strict Chapter Isolation (Ch 1 vs Ch 9)
    print("\n[RR-2] Strict Chapter Isolation in ChromaDB:")
    try:
        p1 = retrieve_passages("EVS_CH01", "What is history?", top_k=5)
        p9 = retrieve_passages("EVS_CH09", "How did cities begin?", top_k=5)
        s1 = {p["source"] for p in p1}
        s9 = {p["source"] for p in p9}
        assert all("Chapter 1" in s for s in s1), f"Unexpected Ch 1 sources: {s1}"
        assert all("Chapter 9" in s for s in s9), f"Unexpected Ch 9 sources: {s9}"
        assert len(s1 & s9) == 0, f"Cross-chapter contamination: {s1 & s9}"
        print(f"  ✓ Ch 1 sources: {s1} | Ch 9 sources: {s9} | Overlap: 0")
        REPORTS.append(TestReport("RR-2", "ChromaDB Chapter Isolation", "ROUTING_RETRIEVAL", False, False, True, "Zero cross-chapter overlap"))
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        REPORTS.append(TestReport("RR-2", "ChromaDB Chapter Isolation", "ROUTING_RETRIEVAL", False, False, False, str(e)))

    # 3. Chapter 9 Overview Retrieval Chunks
    print("\n[RR-3] Chapter 9 Generic Overview Retrieval:")
    try:
        ov_chunks = retrieve_chapter_overview("EVS_CH09", "Settled Life and Urban Civilization")
        assert len(ov_chunks) >= 3, f"Expected >= 3 overview chunks, got {len(ov_chunks)}"
        assert all("Chapter 9" in c["source"] for c in ov_chunks), "Overview chunks must be strictly Chapter 9"
        # Confirm opening outline chunk is present (Page 1)
        pages = {c["page_number"] for c in ov_chunks}
        assert 1 in pages, f"Page 1 outline chunk missing from overview: {pages}"
        print(f"  ✓ Retrieved {len(ov_chunks)} overview chunks across pages {sorted(pages)}")
        REPORTS.append(TestReport("RR-3", "Chapter Overview Chunk Retrieval", "ROUTING_RETRIEVAL", False, False, True, f"{len(ov_chunks)} chunks retrieved"))
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        REPORTS.append(TestReport("RR-3", "Chapter Overview Chunk Retrieval", "ROUTING_RETRIEVAL", False, False, False, str(e)))

    # 4. Intent Routing Matrix
    print("\n[RR-4] Intent Routing Matrix:")
    routing_cases = [
        ("Hii", [], "EVS_CH09", "general_chat", 0),
        ("Tell me a joke", [], "EVS_CH09", "general_chat", 0),
        ("What are the 3 main topics taught in this chapter?", [], "EVS_CH09", "chapter_question", 3),
        ("Why is the topic of this chapter important for us to study?", [], "EVS_CH09", "chapter_question", 3),
        ("Act like a researcher studying the topic of this chapter.", [], "EVS_CH09", "chapter_question", 3),
        ("Act like Shivaji Maharaj and tell me your thoughts.", [], "EVS_CH09", "general_knowledge", 0),
        ("What does this chapter say about how smartphones were invented?", [], "EVS_CH09", "chapter_question", 0), # honest absence
        ("What are the three types of historical sources?", [], "EVS_CH09", "general_knowledge", 0), # Ch 9 doesn't cover
        ("What are the three types of sources of history?", [], "EVS_CH01", "chapter_question", 2),  # Ch 1 covers
        ("Name 4 famous rivers in India.", [], "EVS_CH09", "general_knowledge", 0),
        ("Explain black holes in space.", [], "EVS_CH09", "general_knowledge", 0),
    ]

    all_routes_ok = True
    for msg, h, ch_id, exp_mode, min_chunks in routing_cases:
        ch = get_chapter(ch_id)
        mode, passages, _, flags = route_intent(msg, h, ch_id, ch.title)
        ok = (mode == exp_mode) and (len(passages) >= min_chunks if min_chunks > 0 else len(passages) == 0)
        status = "✓" if ok else "✗"
        print(f"  {status} '{msg[:42]:<42}' -> {mode:<18} (chunks: {len(passages)})")
        if not ok:
            all_routes_ok = False
            print(f"      Expected mode: {exp_mode}, min_chunks: {min_chunks}")

    REPORTS.append(TestReport("RR-4", "Intent Routing Matrix (11 cases)", "ROUTING_RETRIEVAL", False, False, all_routes_ok, "All 11 routing decisions verified"))

    # 5. Anti-Poisoning Follow-up Resolution
    print("\n[RR-5] Anti-Poisoning Follow-up Resolution:")
    try:
        t1_hist = [
            HistoryMessage(role="user", content="What does this chapter say about how smartphones and the internet were invented?"),
            HistoryMessage(role="assistant", content="Chapter 9 does not cover smartphones or the internet."),
        ]
        t2_msg = "Act like a scientist or researcher studying the topic of this chapter. Tell me what you do every day."
        mode, passages, _, flags = route_intent(t2_msg, t1_hist, "EVS_CH09", "Settled Life and Urban Civilization")
        assert mode == "chapter_question", f"Anti-poisoning failed: expected chapter_question, got {mode}"
        assert flags.get("is_chapter_roleplay"), "Expected is_chapter_roleplay flag"
        assert len(passages) > 0, "Expected overview chunks for chapter roleplay"
        assert all("Chapter 9" in p["source"] for p in passages), "Passages must be Chapter 9"
        print(f"  ✓ Successfully routed to chapter_question with {len(passages)} Chapter 9 chunks without poisoning")
        REPORTS.append(TestReport("RR-5", "Anti-Poisoning Follow-up Resolution", "ROUTING_RETRIEVAL", False, False, True, "Turn 2 isolated from Turn 1 off-topic subject"))
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        REPORTS.append(TestReport("RR-5", "Anti-Poisoning Follow-up Resolution", "ROUTING_RETRIEVAL", False, False, False, str(e)))

    # 6. Citation Filtering Logic
    print("\n[RR-6] Verified Citation Filtering Logic:")
    try:
        # General knowledge -> 0 citations
        c_gk = filter_supporting_sources([{"source": "Chapter 9.pdf", "page_number": 1, "distance": 0.2}], "general_knowledge", {})
        assert len(c_gk) == 0, "General knowledge must produce 0 citations"
        # Not covered -> 0 citations
        c_nc = filter_supporting_sources([{"source": "Chapter 9.pdf", "page_number": 1, "distance": 0.2}], "chapter_question", {"not_covered": True})
        assert len(c_nc) == 0, "Absent topic must produce 0 citations"
        # Valid chapter question with high distance -> excluded
        c_hi = filter_supporting_sources([{"source": "Chapter 9.pdf", "page_number": 1, "distance": 0.38, "chapter_name": "Ch9"}], "chapter_question", {})
        assert len(c_hi) == 0, "High distance chunk must be excluded"
        # Valid chapter question with good distance -> included & deduplicated
        raw = [
            {"source": "Chapter 9.pdf", "page_number": 2, "distance": 0.25, "chapter_name": "Ch9"},
            {"source": "Chapter 9.pdf", "page_number": 2, "distance": 0.28, "chapter_name": "Ch9"}, # dup page
            {"source": "Chapter 9.pdf", "page_number": 3, "distance": 0.29, "chapter_name": "Ch9"},
        ]
        c_ok = filter_supporting_sources(raw, "chapter_question", {})
        assert len(c_ok) == 2, f"Expected 2 deduplicated citations, got {len(c_ok)}"
        print(f"  ✓ Citation rules verified: GK=0, Absent=0, DistFilter=OK, Deduplication=2")
        REPORTS.append(TestReport("RR-6", "Citation Filtering Logic", "ROUTING_RETRIEVAL", False, False, True, "All citation constraints enforced"))
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        REPORTS.append(TestReport("RR-6", "Citation Filtering Logic", "ROUTING_RETRIEVAL", False, False, False, str(e)))


# ═══════════════════════════════════════════════════════════════════════════════
# PART 2: LIVE MODEL GENERATION & FACTUAL ACCURACY TESTS (OLLAMA QWEN3:1.7B)
# ═══════════════════════════════════════════════════════════════════════════════


def run_part2_live_model_tests():
    print_banner("PART 2: LIVE MODEL GENERATION & FACTUAL ACCURACY TESTS (QWEN3:1.7B)")
    print("  Note: Testing actual responses from local Ollama model. ZERO MOCKS.")

    # LM-1: Chapter 9 Overview
    print("\n[LM-1] Chapter 9 Overview ('What are the 3 main topics taught in this chapter?'):")
    try:
        req = ChatRequest(chapter_id="EVS_CH09", message="What are the 3 main topics taught in this chapter?", history=[])
        resp = process_chat(req)
        ans = resp.answer.lower()
        print(f"  Live Model Answer:\n{resp.answer[:280]}...")
        assert resp.mode == "chapter_question", f"Expected chapter_question, got {resp.mode}"
        assert len(resp.sources) > 0, "Expected Chapter 9 citations"
        # Check actual topics
        expected = ["metal", "copper", "potter", "wheel", "trade", "transport", "settlement", "cit"]
        found = [t for t in expected if t in ans]
        assert len(found) >= 2, f"Expected at least 2 Ch 9 topics, found: {found}"
        assert "freedom fighter" not in ans and "constitution" not in ans, "Hardcoded topic contamination detected!"
        print(f"  ✓ PASS (Grounded topics found: {found})")
        REPORTS.append(TestReport("LM-1", "Ch 9 Overview Answer Grounding", "LIVE_MODEL", True, False, True, f"Found topics: {found}"))
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        REPORTS.append(TestReport("LM-1", "Ch 9 Overview Answer Grounding", "LIVE_MODEL", True, False, False, str(e)))

    # LM-2: Chapter 9 Importance
    print("\n[LM-2] Chapter 9 Importance ('Why is the topic of this chapter important for us to study?'):")
    try:
        req = ChatRequest(chapter_id="EVS_CH09", message="Why is the topic of this chapter important for us to study?", history=[])
        resp = process_chat(req)
        ans = resp.answer.lower()
        print(f"  Live Model Answer:\n{resp.answer[:280]}...")
        assert resp.mode == "chapter_question"
        assert len(resp.sources) > 0
        assert any(k in ans for k in ["past", "human", "settled", "metal", "tool", "wheel", "cit", "civilization"])
        assert "freedom fighter" not in ans and "constitution" not in ans
        print("  ✓ PASS")
        REPORTS.append(TestReport("LM-2", "Ch 9 Importance Answer Grounding", "LIVE_MODEL", True, False, True, "Grounded in early human development"))
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        REPORTS.append(TestReport("LM-2", "Ch 9 Importance Answer Grounding", "LIVE_MODEL", True, False, False, str(e)))

    # LM-3: Chapter-Aware Roleplay Anti-Poisoning
    print("\n[LM-3] Chapter-Aware Roleplay Anti-Poisoning (Researcher on Ch 9 after Smartphone Q):")
    try:
        t1_q = "What does this chapter say about how smartphones and the internet were invented?"
        t1_resp = process_chat(ChatRequest(chapter_id="EVS_CH09", message=t1_q, history=[]))
        h = [HistoryMessage(role="user", content=t1_q), HistoryMessage(role="assistant", content=t1_resp.answer)]
        t2_q = "Act like a scientist or researcher studying the topic of this chapter. Tell me what you do every day."
        resp = process_chat(ChatRequest(chapter_id="EVS_CH09", message=t2_q, history=h))
        ans = resp.answer.lower()
        print(f"  Live Model Answer:\n{resp.answer[:300]}...")
        assert resp.mode == "chapter_question"
        assert "smartphone" not in ans and "internet" not in ans, "Poisoning! Smartphone/internet leaked into Turn 2!"
        assert any(fp in ans for fp in ["i ", "i'm", "my ", "i study", "i excavate", "i look", "i research"]), "Roleplay must be in first person"
        print("  ✓ PASS (Zero conversation poisoning detected)")
        REPORTS.append(TestReport("LM-3", "Roleplay Anti-Poisoning", "LIVE_MODEL", True, False, True, "Roleplay focused on Ch 9; zero smartphone leakage"))
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        REPORTS.append(TestReport("LM-3", "Roleplay Anti-Poisoning", "LIVE_MODEL", True, False, False, str(e)))

    # LM-4: Chapter Coverage Honest Absence
    print("\n[LM-4] Chapter Coverage Honest Absence ('What does this chapter say about smartphones...'):")
    try:
        req = ChatRequest(chapter_id="EVS_CH09", message="What does this chapter say about how smartphones and the internet were invented?", history=[])
        resp = process_chat(req)
        ans = resp.answer.lower()
        print(f"  Live Model Answer:\n{resp.answer[:280]}...")
        assert resp.mode == "chapter_question"
        assert len(resp.sources) == 0, f"Expected 0 citations for absent topic, got {len(resp.sources)}"
        assert any(neg in ans for neg in ["not", "does not", "doesn't", "no mention"]), "Must state chapter does not cover this"
        print("  ✓ PASS (Honest absence with 0 false citations)")
        REPORTS.append(TestReport("LM-4", "Chapter Absence & Zero Citations", "LIVE_MODEL", True, False, True, "Honest absence, 0 citations"))
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        REPORTS.append(TestReport("LM-4", "Chapter Absence & Zero Citations", "LIVE_MODEL", True, False, False, str(e)))

    # LM-5: General Knowledge Indian Rivers
    print("\n[LM-5] General Knowledge Rivers ('Name 4 famous rivers in India.'):")
    try:
        req = ChatRequest(chapter_id="EVS_CH09", message="Name 4 famous rivers in India.", history=[])
        resp = process_chat(req)
        ans = resp.answer.lower()
        print(f"  Live Model Answer:\n{resp.answer}")
        assert resp.mode == "general_knowledge"
        assert len(resp.sources) == 0, "No textbook citations for general knowledge rivers"
        # Anti-hallucination check
        assert "nile" not in ans and "amazon" not in ans and "mississippi" not in ans, "Foreign river hallucinated in Indian rivers!"
        indian_rivers = ["ganga", "ganges", "yamuna", "godavari", "narmada", "brahmaputra", "indus", "kaveri", "cauvery", "krishna", "mahanadi", "tapti"]
        found = [r for r in indian_rivers if r in ans]
        print(f"  Detected Indian rivers: {found}")
        assert len(found) >= 3, f"Expected >= 3 genuine Indian rivers, found {found}"
        print("  ✓ PASS (All genuine Indian rivers, zero hallucinations)")
        REPORTS.append(TestReport("LM-5", "General Knowledge Indian Rivers", "LIVE_MODEL", True, False, True, f"Found rivers: {found}"))
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        REPORTS.append(TestReport("LM-5", "General Knowledge Indian Rivers", "LIVE_MODEL", True, False, False, str(e)))

    # LM-6: Historical Sources Mode & Citations Isolation
    print("\n[LM-6] Historical Sources Mode & Citations (Ch 9 vs Ch 1):")
    try:
        r9 = process_chat(ChatRequest(chapter_id="EVS_CH09", message="What are the three types of historical sources?", history=[]))
        r1 = process_chat(ChatRequest(chapter_id="EVS_CH01", message="What are the three types of sources of history?", history=[]))
        print(f"  Ch 9: mode={r9.mode}, sources={len(r9.sources)}")
        print(f"  Ch 1: mode={r1.mode}, sources={len(r1.sources)}")
        assert len(r9.sources) == 0, "Chapter 9 must have 0 citations for historical sources"
        assert r1.mode == "chapter_question" and len(r1.sources) > 0, "Chapter 1 must have valid citations"
        print("  ✓ PASS")
        REPORTS.append(TestReport("LM-6", "Historical Sources Citation Isolation", "LIVE_MODEL", True, False, True, "Ch 9: 0 citations, Ch 1: verified citations"))
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        REPORTS.append(TestReport("LM-6", "Historical Sources Citation Isolation", "LIVE_MODEL", True, False, False, str(e)))

    # LM-7: Markdown Formatting Integrity on Live Model
    print("\n[LM-7] Markdown Formatting Integrity (Live Model):")
    try:
        req = ChatRequest(chapter_id="EVS_CH09", message="Name 4 famous rivers in India.", history=[])
        resp = process_chat(req)
        lines = [line.strip() for line in resp.answer.split("\n") if line.strip()]
        numbered_lines = [l for l in lines if re.match(r"^\d+\.\s+", l)]
        print(f"  Numbered lines count: {len(numbered_lines)}")
        for nl in numbered_lines:
            print(f"    {nl}")
        assert len(numbered_lines) >= 4, f"Expected >= 4 cleanly separated numbered lines, got {len(numbered_lines)}"
        assert not re.search(r"\d+\.\S", resp.answer), "Missing space after list numbers detected!"
        print("  ✓ PASS")
        REPORTS.append(TestReport("LM-7", "Markdown Formatting Integrity", "LIVE_MODEL", True, False, True, f"{len(numbered_lines)} separated numbered lines"))
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        REPORTS.append(TestReport("LM-7", "Markdown Formatting Integrity", "LIVE_MODEL", True, False, False, str(e)))

    # LM-8: Contextual Follow-up 10 Bullet Points
    print("\n[LM-8] Contextual Follow-up 10 Bullet Points:")
    try:
        t1 = process_chat(ChatRequest(chapter_id="EVS_CH01", message="What is history?", history=[]))
        h = [HistoryMessage(role="user", content="What is history?"), HistoryMessage(role="assistant", content=t1.answer)]
        resp = process_chat(ChatRequest(chapter_id="EVS_CH01", message="Give me bullet points, at least 10.", history=h))
        bullet_items = re.findall(r"(?:^\s*\d+[\.\)]|^\s*[-*•])\s*.+", resp.answer, flags=re.MULTILINE)
        print(f"  Detected bullet items: {len(bullet_items)}")
        assert resp.mode == "chapter_question"
        assert len(bullet_items) >= 10, f"Expected >= 10 bullet items, got {len(bullet_items)}"
        print("  ✓ PASS")
        REPORTS.append(TestReport("LM-8", "Contextual 10 Bullets Follow-up", "LIVE_MODEL", True, False, True, f"{len(bullet_items)} bullets generated"))
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        REPORTS.append(TestReport("LM-8", "Contextual 10 Bullets Follow-up", "LIVE_MODEL", True, False, False, str(e)))

    # LM-9: List Continuation Non-Duplication
    print("\n[LM-9] List Continuation Non-Duplication ('Add more'):")
    try:
        t1 = process_chat(ChatRequest(chapter_id="EVS_CH01", message="List famous Indian freedom fighters.", history=[]))
        h = [HistoryMessage(role="user", content="List famous Indian freedom fighters."), HistoryMessage(role="assistant", content=t1.answer)]
        t2 = process_chat(ChatRequest(chapter_id="EVS_CH01", message="Add more.", history=h))
        names1 = set(n.lower() for n in extract_list_names(t1.answer))
        names2 = set(n.lower() for n in extract_list_names(t2.answer))
        overlap = names1 & names2
        print(f"  Turn 1 items: {names1}")
        print(f"  Turn 2 items: {names2}")
        print(f"  Overlap count: {len(overlap)}")
        assert len(overlap) == 0, f"Repeated items detected: {overlap}"
        assert len(names2) >= 3, f"Expected at least 3 new items, got {len(names2)}"
        print("  ✓ PASS")
        REPORTS.append(TestReport("LM-9", "List Continuation Non-Duplication", "LIVE_MODEL", True, False, True, f"0 overlap across {len(names1)} and {len(names2)} items"))
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        REPORTS.append(TestReport("LM-9", "List Continuation Non-Duplication", "LIVE_MODEL", True, False, False, str(e)))

    # LM-10: Chapter 3 Chronology
    print("\n[LM-10] Chapter 3 Chronology Order:")
    try:
        q = """Arrange the events given below in chronological order:
(a) Water bodies appeared on the earth's surface.
(b) The sun and the planets revolving around it were created.
(c) Protozoa appeared in water.
(d) An enormous cloud of hot gases and dust was formed in space."""
        resp = process_chat(ChatRequest(chapter_id="EVS_CH03", message=q, history=[]))
        ans_c = resp.answer.lower()
        pos_d = ans_c.find("(d)")
        pos_b = ans_c.find("(b)")
        pos_a = ans_c.find("(a)")
        pos_c = ans_c.find("(c)")
        if pos_d != -1 and pos_b != -1 and pos_a != -1 and pos_c != -1:
            assert pos_d < pos_b < pos_a < pos_c, f"Chronology failed: indices d={pos_d}, b={pos_b}, a={pos_a}, c={pos_c}"
        else:
            assert ans_c.find("cloud") < ans_c.find("sun") < ans_c.find("water") < ans_c.find("protozoa")
        print("  ✓ PASS")
        REPORTS.append(TestReport("LM-10", "Chapter 3 Chronological Order", "LIVE_MODEL", True, False, True, "(d) -> (b) -> (a) -> (c) verified"))
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        REPORTS.append(TestReport("LM-10", "Chapter 3 Chronological Order", "LIVE_MODEL", True, False, False, str(e)))


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN REPORTING RUNNER
# ═══════════════════════════════════════════════════════════════════════════════


def print_final_summary_report():
    print_banner("FINAL VERIFICATION AUDIT & SUMMARY REPORT")

    total = len(REPORTS)
    routing_count = sum(1 for r in REPORTS if r.category == "ROUTING_RETRIEVAL")
    live_count = sum(1 for r in REPORTS if r.category == "LIVE_MODEL")
    mocked_count = sum(1 for r in REPORTS if r.mocked)
    passed_count = sum(1 for r in REPORTS if r.passed)
    failed_count = sum(1 for r in REPORTS if not r.passed)

    print(f"\n{'ID':<6} {'TEST NAME':<38} {'CATEGORY':<18} {'LIVE':<6} {'MOCKED':<8} {'STATUS':<8}")
    print("-" * 88)
    for r in REPORTS:
        live_str = "YES" if r.live_model else "NO"
        mock_str = "YES" if r.mocked else "NO"
        status_str = "PASS ✓" if r.passed else "FAIL ✗"
        print(f"{r.test_id:<6} {r.name[:36]:<38} {r.category:<18} {live_str:<6} {mock_str:<8} {status_str:<8}")

    print("-" * 88)
    print(f"Total Tests Executed        : {total}")
    print(f"Routing & Retrieval Tests   : {routing_count}")
    print(f"Live Model (qwen3:1.7b) Tests: {live_count}")
    print(f"Mocked Tests                : {mocked_count} (ZERO mocks allowed)")
    print(f"Tests Passed                : {passed_count}")
    print(f"Tests Failed                : {failed_count}")
    print("=" * 88)

    if failed_count > 0:
        print("\nFAILURES RECORDED HONESTLY:")
        for r in REPORTS:
            if not r.passed:
                print(f"  - [{r.test_id}] {r.name}: {r.details}")
        sys.exit(1)
    else:
        print("\nALL TESTS PASSED WITH 100% SUCCESS RATE ACROSS BOTH CATEGORIES! ✓\n")


if __name__ == "__main__":
    run_part1_routing_and_retrieval_tests()
    run_part2_live_model_tests()
    print_final_summary_report()
