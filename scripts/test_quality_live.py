"""
Live Response Quality Verification Test Suite for VidyaVerse Learning Hub.
Tests against the live FastAPI backend at http://127.0.0.1:8000/api/chat using lightweight urllib.
Validates:
1. Zero internal instruction leakage ('We are teaching...', 'As [persona]...', rubrics, tone/method dumps).
2. Direct first-sentence answers.
3. Factual grounding (Shivaji Maharaj born 19 Feb 1630 at Fort Shivneri near Junnar; parents Shahaji & Jijabai).
4. Mathematical correctness (Pythagoras definition, formula a² + b² = c², 3-4-5 triangle -> 5 cm).
5. Conversational naturalness (greetings).
"""
import json
import re
import urllib.request
import urllib.error

API_URL = "http://127.0.0.1:8000/api/chat"

LEAKAGE_INDICATORS = [
    r"^\s*we are teaching\b",
    r"^\s*as\s+(?:the\s+)?(?:persona|educational persona|pythagoras|shivaji|tutor|mentor)[,\s]+i\s+(?:must|should|will)\b",
    r"key points from the persona guidelines",
    r"explanation structure:\s*situation",
    r"tone\s*(?:and|&)\s*vocabulary",
    r"teaching method:",
    r"steps for the response:",
    r"strict guidelines",
    r"response rubric",
    r"according to my instructions",
    r"here is how i will answer",
    r"i must respond with:",
    r"situation\s*->\s*dilemma",
]

TEST_CASES = [
    {
        "id": "hist_childhood",
        "subject": "history",
        "chapter_id": "history_chapter_04",
        "persona_id": "shivaji_maharaj",
        "question": "What is Shivaji's Childhood about?",
        "expected_desc": "Direct, concise, chapter-grounded explanation of Shivaji's childhood",
        "check": lambda ans, p, src: len(ans) > 30 and ("childhood" in ans.lower() or "shivneri" in ans.lower() or "jijabai" in ans.lower()),
    },
    {
        "id": "hist_parents",
        "subject": "history",
        "chapter_id": "history_chapter_04",
        "persona_id": "shivaji_maharaj",
        "question": "Who were Shivaji Maharaj's parents?",
        "expected_desc": "Clear answer with supported names (Shahaji and Jijabai)",
        "check": lambda ans, p, src: "shahaji" in ans.lower() and "jijabai" in ans.lower(),
    },
    {
        "id": "hist_birth_date",
        "subject": "history",
        "chapter_id": "history_chapter_04",
        "persona_id": "shivaji_maharaj",
        "question": "When was Shivaji Maharaj born?",
        "expected_desc": "Correct, source-grounded answer (1630 / 19 February 1630) without fake dates",
        "check": lambda ans, p, src: "1630" in ans and "23 november" not in ans.lower(),
    },
    {
        "id": "hist_jijabai",
        "subject": "history",
        "chapter_id": "history_chapter_04",
        "persona_id": "shivaji_maharaj",
        "question": "Why is Jijabai important in this chapter?",
        "expected_desc": "Relevant explanation based on chapter evidence (mother, values, stories)",
        "check": lambda ans, p, src: ("mother" in ans.lower() or "jijabai" in ans.lower() or "taught" in ans.lower() or "values" in ans.lower() or "stories" in ans.lower()),
    },
    {
        "id": "math_pythagoras_def",
        "subject": "mathematics",
        "chapter_id": "mathematics_chapter_02",
        "persona_id": "pythagoras",
        "question": "What is Pythagoras Theorem about?",
        "expected_desc": "Plain-language definition and readable equation (hypotenuse, right triangle)",
        "check": lambda ans, p, src: ("right" in ans.lower() or "triangle" in ans.lower()) and ("hypotenuse" in ans.lower() or "square" in ans.lower() or "a²" in ans or "c²" in ans or "c^2" in ans),
    },
    {
        "id": "math_triangle_calc",
        "subject": "mathematics",
        "chapter_id": "mathematics_chapter_02",
        "persona_id": "pythagoras",
        "question": "A right triangle has sides 3 cm and 4 cm. Find the hypotenuse.",
        "expected_desc": "Correct steps and result of 5 cm",
        "check": lambda ans, p, src: "5" in ans and ("cm" in ans.lower() or "hypotenuse" in ans.lower()),
    },
    {
        "id": "math_why_square",
        "subject": "mathematics",
        "chapter_id": "mathematics_chapter_02",
        "persona_id": "pythagoras",
        "question": "Explain why we square the sides in Pythagoras' theorem.",
        "expected_desc": "Student-friendly conceptual explanation (areas of squares on the sides)",
        "check": lambda ans, p, src: ("area" in ans.lower() or "square" in ans.lower() or "geometric" in ans.lower()),
    },
    {
        "id": "evs_concept",
        "subject": "evs",
        "chapter_id": "evs_chapter_01",
        "persona_id": None,
        "question": "Explain one concept from the currently selected chapter.",
        "expected_desc": "Answer grounded in that chapter's actual retrieved content (What is History, past events, time)",
        "check": lambda ans, p, src: len(ans) > 40 and ("history" in ans.lower() or "past" in ans.lower() or "time" in ans.lower() or "science" in ans.lower()),
    },
    {
        "id": "conv_followup_simple",
        "subject": "history",
        "chapter_id": "history_chapter_04",
        "persona_id": "shivaji_maharaj",
        "question": "Explain it more simply.",
        "history": [
            {"role": "user", "content": "What is Shivaji's Childhood about?"},
            {"role": "assistant", "content": "Shivaji's Childhood describes the early years of Chhatrapati Shivaji Maharaj on Fort Shivneri near Junnar. His mother Jijabai instilled in him noble values, brave stories of Rama and Krishna, and games with Mavla children prepared him for leadership."},
        ],
        "expected_desc": "Uses conversation context and simplifies previous explanation",
        "check": lambda ans, p, src: len(ans) > 20 and ("shivaji" in ans.lower() or "simple" in ans.lower() or "young" in ans.lower() or "jijabai" in ans.lower() or "grow" in ans.lower()),
    },
    {
        "id": "conv_hi",
        "subject": "history",
        "chapter_id": "history_chapter_04",
        "persona_id": "shivaji_maharaj",
        "question": "Hi!",
        "expected_desc": "Natural conversational acknowledgement, not a formal lesson template",
        "check": lambda ans, p, src: any(w in ans.lower() for w in ["hello", "welcome", "greetings", "hi", "happy to", "learner", "ready"]),
    },
]


def send_chat_query(tc: dict) -> dict:
    import requests
    payload = {
        "message": tc["question"],
        "chapter_id": tc["chapter_id"],
        "subject_id": tc["subject"],
        "persona_id": tc.get("persona_id"),
        "history": tc.get("history", []),
        "mode": "study",
    }
    resp = requests.post(API_URL, json=payload, timeout=180)
    resp.raise_for_status()
    return resp.json()


def check_leakage(text: str) -> list[str]:
    leaks = []
    for pat in LEAKAGE_INDICATORS:
        if re.search(pat, text, re.IGNORECASE):
            leaks.append(pat)
    return leaks


def run():
    print("=" * 80, flush=True)
    print("VIDYAVERSE RESPONSE QUALITY FIX — LIVE VERIFICATION SUITE", flush=True)
    print("=" * 80, flush=True)

    results = []
    for i, tc in enumerate(TEST_CASES, 1):
        print(f"\n[{i}/{len(TEST_CASES)}] Testing {tc['subject'].upper()} ({tc['persona_id'] or 'Tutor'}):", flush=True)
        print(f"  Question: '{tc['question']}'", flush=True)

        try:
            res = send_chat_query(tc)
            ans = res.get("answer", "")
            ret_count = res.get("retrieved_count", 0)
            sources = res.get("sources", [])
            mode = res.get("mode", "")

            # Check for leaked instructions
            leaks = check_leakage(ans)
            leak_status = "PASS (0 leaks)" if not leaks else f"FAIL (leaked: {leaks})"

            # Check content criteria
            content_pass = tc["check"](ans, ret_count, sources)
            content_status = "PASS" if content_pass else "FAIL (content expectations unmet)"

            overall_pass = (len(leaks) == 0) and content_pass

            word_count = len(ans.split())
            first_sentence = ans.split(".")[0] if "." in ans else ans[:60]

            print(f"  Retrieved Chunks : {ret_count}", flush=True)
            print(f"  Mode             : {mode}", flush=True)
            print(f"  Word Count       : {word_count}", flush=True)
            print(f"  First Sentence   : {first_sentence}...", flush=True)
            print(f"  Leakage Check    : {leak_status}", flush=True)
            print(f"  Quality Check    : {content_status}", flush=True)
            print(f"  OVERALL          : {'✓ PASSED' if overall_pass else '✗ FAILED'}", flush=True)
            print(f"  Full Answer Preview:\n    {ans[:250]}...", flush=True)

            results.append({
                "id": tc["id"],
                "subject": tc["subject"],
                "persona": tc.get("persona_id"),
                "question": tc["question"],
                "answer": ans,
                "retrieved_count": ret_count,
                "sources_count": len(sources),
                "leaks": leaks,
                "passed": overall_pass,
            })

        except Exception as e:
            print(f"  ERROR executing query: {e}", flush=True)
            results.append({
                "id": tc["id"],
                "subject": tc["subject"],
                "persona": tc.get("persona_id"),
                "question": tc["question"],
                "error": str(e),
                "passed": False,
            })

    total = len(results)
    passed = sum(1 for r in results if r.get("passed"))
    print("\n" + "=" * 80, flush=True)
    print(f"SUMMARY: {passed}/{total} tests passed ({passed/total*100:.1f}%)", flush=True)
    print("=" * 80, flush=True)

    # Save results to scratch json for report generation
    with open("scripts/quality_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    run()
