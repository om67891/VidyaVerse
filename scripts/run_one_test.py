import requests
import json
import sys

payload = {
    "message": sys.argv[1] if len(sys.argv) > 1 else "What is Shivaji's Childhood about?",
    "chapter_id": sys.argv[2] if len(sys.argv) > 2 else "history_chapter_04",
    "subject_id": sys.argv[3] if len(sys.argv) > 3 else "history",
    "persona_id": sys.argv[4] if len(sys.argv) > 4 else "shivaji_maharaj",
    "history": [],
    "mode": "study",
}

print(f"Sending query: '{payload['message']}' (chapter: {payload['chapter_id']}, persona: {payload['persona_id']})")
try:
    resp = requests.post("http://127.0.0.1:8000/api/chat", json=payload, timeout=180)
    resp.raise_for_status()
    data = resp.json()
    print("STATUS: SUCCESS")
    print(f"RETRIEVED CHUNKS: {data.get('retrieved_count')}")
    print(f"MODE: {data.get('mode')}")
    print("--- ANSWER ---")
    print(data.get("answer"))
    print("--- SOURCES ---")
    print(json.dumps(data.get("sources", []), indent=2))
except Exception as e:
    print(f"ERROR: {e}")
