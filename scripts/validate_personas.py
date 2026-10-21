"""
Validate all persona profiles against personas/schema/persona.schema.json
and verify that all referenced avatars, sources, and examples exist.
"""
from __future__ import annotations

import json
from pathlib import Path
import jsonschema

ROOT = Path(__file__).resolve().parent.parent
PERSONAS_DIR = ROOT / "personas"
SCHEMA_PATH = PERSONAS_DIR / "schema" / "persona.schema.json"
FRONTEND_PUBLIC = ROOT / "frontend" / "public"


def validate_all_personas():
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema not found at {SCHEMA_PATH}")

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft7Validator(schema)

    errors_found = 0
    personas_validated = 0
    total_examples = 0

    subjects = ["history", "mathematics", "evs"]
    for sub in subjects:
        sub_dir = PERSONAS_DIR / sub
        index_file = sub_dir / "index.json"
        if not index_file.exists():
            print(f"[FAIL] Missing index.json for subject {sub}")
            errors_found += 1
            continue

        index_data = json.loads(index_file.read_text(encoding="utf-8"))
        print(f"\n--- Validating Subject: {sub.upper()} ({index_data.get('total_personas')} personas) ---")

        for entry in index_data.get("personas", []):
            p_id = entry["persona_id"]
            p_dir = sub_dir / p_id
            profile_file = p_dir / "profile.json"

            if not profile_file.exists():
                print(f"  ✗ [{p_id}] Missing profile.json at {profile_file}")
                errors_found += 1
                continue

            try:
                profile = json.loads(profile_file.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"  ✗ [{p_id}] JSON syntax error in profile.json: {e}")
                errors_found += 1
                continue

            # Schema validation
            validation_errors = list(validator.iter_errors(profile))
            if validation_errors:
                print(f"  ✗ [{p_id}] Schema validation failed with {len(validation_errors)} errors:")
                for err in validation_errors:
                    print(f"      - {err.message} (at {list(err.path)})")
                errors_found += len(validation_errors)
                continue

            # Verify Avatar exists
            avatar_path = profile.get("avatar_path", "")
            if avatar_path.startswith("/"):
                disk_avatar = FRONTEND_PUBLIC / avatar_path.lstrip("/")
            else:
                disk_avatar = FRONTEND_PUBLIC / avatar_path

            if not disk_avatar.exists():
                print(f"  ✗ [{p_id}] Referenced avatar not found on disk: {disk_avatar}")
                errors_found += 1
                continue

            # Verify Sources file exists
            sources_file = p_dir / profile.get("sources_file", "sources.json")
            if not sources_file.exists():
                print(f"  ✗ [{p_id}] Missing sources file: {sources_file}")
                errors_found += 1
                continue
            sources_data = json.loads(sources_file.read_text(encoding="utf-8"))
            if not sources_data.get("primary_sources"):
                print(f"  ✗ [{p_id}] Sources file lacks primary_sources")
                errors_found += 1
                continue

            # Verify Examples file exists and has >= 3 examples
            examples_file = p_dir / profile.get("examples_file", "examples.jsonl")
            if not examples_file.exists():
                print(f"  ✗ [{p_id}] Missing examples file: {examples_file}")
                errors_found += 1
                continue

            lines = [line.strip() for line in examples_file.read_text(encoding="utf-8").splitlines() if line.strip()]
            if len(lines) < 3:
                print(f"  ✗ [{p_id}] Needs at least 3 examples in examples.jsonl, found {len(lines)}")
                errors_found += 1
                continue

            # Parse each example line
            ex_err = False
            for idx, l in enumerate(lines, 1):
                try:
                    ex_obj = json.loads(l)
                    if not ex_obj.get("user_prompt") or not ex_obj.get("example_response"):
                        print(f"  ✗ [{p_id}] Example #{idx} missing user_prompt or example_response")
                        errors_found += 1
                        ex_err = True
                except Exception as e:
                    print(f"  ✗ [{p_id}] Example #{idx} JSON parse error: {e}")
                    errors_found += 1
                    ex_err = True

            if ex_err:
                continue

            total_examples += len(lines)
            personas_validated += 1
            print(f"  ✓ [{p_id}] {profile['display_name']} — PASS (Schema OK, Avatar OK, {len(lines)} examples, Sources OK)")

    print("\n" + "=" * 65)
    print("  PERSONA CATALOGUE VALIDATION AUDIT")
    print("=" * 65)
    print(f"  Personas Validated: {personas_validated} / 24")
    print(f"  Total Examples Verified: {total_examples}")
    print(f"  Errors Detected: {errors_found}")
    print("=" * 65)

    if errors_found > 0:
        raise ValueError(f"Persona catalogue validation failed with {errors_found} errors.")
    else:
        print("  100% OF PERSONA PROFILES PASSED SCHEMA & CONTENT INTEGRITY! ✓\n")


if __name__ == "__main__":
    validate_all_personas()
