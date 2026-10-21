#!/usr/bin/env python3
"""
VidyaVerse Part 05 — End-to-End Smoke Test Suite
Tests: model availability, API health, frontend build, chat endpoints, visual components.

Usage:
    python scripts/test_part5_smoke.py
"""
from __future__ import annotations

import sys
import json
import time
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_URL = "http://localhost:8000"

PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
INFO = "\033[94mℹ\033[0m"

results: list[dict] = []


def record(name: str, passed: bool, detail: str = "") -> None:
    results.append({"name": name, "passed": passed, "detail": detail})
    symbol = PASS if passed else FAIL
    suffix = f"  [{detail}]" if detail else ""
    print(f"  {symbol}  {name}{suffix}")


def section(title: str) -> None:
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")


# ── 1. Ollama Model Availability ──────────────────────────────────────────────

section("1. Ollama Model Availability")

try:
    import subprocess
    result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
    output = result.stdout + result.stderr
    has_4b = "qwen3:4b" in output
    has_1_7b = "qwen3:1.7b" in output
    record("qwen3:4b available", has_4b, output.strip().split("\n")[0] if not has_4b else "ready")
    if not has_4b and has_1_7b:
        record("qwen3:1.7b fallback available", True, "Using 1.7b while 4b downloads")
    elif not has_4b:
        record("Any Ollama model available", False, "No qwen3 model found")
except Exception as e:
    record("Ollama CLI accessible", False, str(e))

# ── 2. API Health Check ────────────────────────────────────────────────────────

section("2. Backend API Health")

try:
    import urllib.request
    import urllib.error

    def api_get(path: str) -> dict:
        req = urllib.request.Request(f"{BACKEND_URL}{path}")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())

    health = api_get("/api/health")
    record("Backend reachable", True, f"status={health.get('status', '?')}")
    record("Ollama reported OK", health.get("ollama_running", False), health.get("model", "?"))
    record("Database reported OK", health.get("status") == "ok", "FastAPI healthy")

except urllib.error.URLError as e:
    record("Backend reachable", False, f"Backend not running — start with: uvicorn backend.main:app --reload")
    print(f"\n  {INFO} To start: cd {PROJECT_ROOT} && uvicorn backend.main:app --reload --port 8000")
    # Skip remaining API tests
    api_available = False
else:
    api_available = True

# ── 3. Subject Catalog Endpoints ──────────────────────────────────────────────

section("3. Subject Catalog Endpoints")

if api_available:
    try:
        subjects = api_get("/api/subjects")
        record("GET /api/subjects", True, f"{len(subjects)} subjects")
        subject_ids = [s["subject_id"] for s in subjects]
        record("History subject present", "history" in subject_ids)
        record("Mathematics subject present", "mathematics" in subject_ids)
        record("EVS subject present", "evs" in subject_ids)
    except Exception as e:
        record("GET /api/subjects", False, str(e))

    for subj_id in ["history", "mathematics", "evs"]:
        try:
            sub = api_get(f"/api/subjects/{subj_id}")
            chapters = sub.get("chapters", [])
            record(f"  {subj_id} chapters loaded", len(chapters) > 0, f"{len(chapters)} chapters")
        except Exception as e:
            record(f"  GET /api/subjects/{subj_id}", False, str(e))

# ── 4. Persona Endpoints ───────────────────────────────────────────────────────

section("4. Persona Catalogue Endpoints")

if api_available:
    for subj_id in ["history", "mathematics", "evs"]:
        try:
            personas = api_get(f"/api/personas?subject_id={subj_id}")
            record(f"  {subj_id} personas loaded", len(personas) >= 2, f"{len(personas)} personas")
        except Exception as e:
            record(f"  personas/{subj_id}", False, str(e))

# ── 5. Chat Endpoint ───────────────────────────────────────────────────────────

section("5. Chat Endpoint (Live Model)")

if api_available:
    test_queries = [
        ("history", "Who was Chhatrapati Shivaji Maharaj?"),
        ("mathematics", "What is an angle?"),
        ("evs", "What is history?"),
    ]

    for subj_id, question in test_queries:
        try:
            sub_info = api_get(f"/api/subjects/{subj_id}")
            chaps = sub_info.get("chapters", [])
            chapter_id = chaps[0]["chapter_id"] if chaps else f"{subj_id}_chapter_01"

            data = json.dumps({
                "chapter_id": chapter_id,
                "subject_id": subj_id,
                "message": question,
                "mode": "study",
            }).encode()
            req = urllib.request.Request(
                f"{BACKEND_URL}/api/chat",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                res = json.loads(resp.read())
            answer = res.get("answer", "")
            record(
                f"  {subj_id} chat response ({chapter_id})",
                len(answer) > 20,
                f"{len(answer)} chars"
            )
        except Exception as e:
            record(f"  {subj_id} chat response", False, str(e))

# ── 6. Frontend Build Artifacts ────────────────────────────────────────────────

section("6. Frontend Build Artifacts")

next_dir = PROJECT_ROOT / "frontend" / ".next"
record("Next.js .next dir exists", next_dir.exists())

build_files = [
    ("components/RichMarkdown.tsx", "Rich markdown renderer"),
    ("components/VisualLearning/MathProofRenderer.tsx", "Math proof component"),
    ("components/VisualLearning/HistoricalTimeline.tsx", "Historical timeline component"),
    ("components/VisualLearning/InteractiveQuizCard.tsx", "Interactive quiz card"),
    ("components/VisualLearning/ConceptMap.tsx", "Concept map component"),
    ("components/ChatSidebar.tsx", "Chat sidebar with scope isolation"),
]

for rel_path, desc in build_files:
    full = PROJECT_ROOT / "frontend" / rel_path
    record(f"  {desc}", full.exists(), rel_path)

# ── 7. Visual Learning Component File Check ────────────────────────────────────

section("7. Visual Learning Components")

vl_dir = PROJECT_ROOT / "frontend" / "components" / "VisualLearning"
vl_files = list(vl_dir.glob("*.tsx")) + list(vl_dir.glob("*.ts"))
record("VisualLearning directory exists", vl_dir.exists())
record(f"  Component files found", len(vl_files) >= 4, f"{len(vl_files)} files")

# ── 8. Backend Services Check ─────────────────────────────────────────────────

section("8. Backend Service Modules")

service_files = [
    "backend/services/tutoring_service.py",
    "backend/services/retrieval_service.py",
    "backend/services/citation_validator.py",
    "backend/services/math_validator.py",
    "backend/services/glossary_service.py",
    "backend/services/quiz_service.py",
    "backend/services/learning_map_service.py",
    "backend/repositories/conversation_repository.py",
]

for rel_path in service_files:
    full = PROJECT_ROOT / rel_path
    record(f"  {Path(rel_path).name}", full.exists())

# ── 9. Config Check ────────────────────────────────────────────────────────────

section("9. Configuration Check")

try:
    sys.path.insert(0, str(PROJECT_ROOT))
    from backend.config import settings
    record("Config module imports OK", True)
    record("ollama_model set", bool(settings.ollama_model), settings.ollama_model)
    is_4b = settings.ollama_model == "qwen3:4b"
    record("qwen3:4b configured", is_4b, settings.ollama_model)
    record("Database path exists", settings.database_path.parent.exists())
except Exception as e:
    record("Config module imports OK", False, str(e))

# ── Summary ────────────────────────────────────────────────────────────────────

section("Summary")

total = len(results)
passed = sum(1 for r in results if r["passed"])
failed = total - passed

print(f"\n  Total: {total} | {PASS} Passed: {passed} | {FAIL} Failed: {failed}")

if failed > 0:
    print(f"\n  Failed checks:")
    for r in results:
        if not r["passed"]:
            print(f"    - {r['name']}: {r['detail']}")

print()
sys.exit(0 if failed == 0 else 1)
