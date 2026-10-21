"""
Textbook Segmentation and Manifest Generation Engine.
Slices master PDFs into chapter PDFs using lossless PyMuPDF page copying,
validates output, and generates structured chapter manifests.
"""
from __future__ import annotations
import os
import sys
import shutil
import hashlib
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
import fitz  # PyMuPDF

from scripts.textbooks.extract_chapter_boundaries import (
    HISTORY_CHAPTERS,
    MATHEMATICS_CHAPTERS,
    EVS_CHAPTERS,
)
from scripts.textbooks.validate_chapter_pdfs import (
    compute_sha256,
    validate_single_chapter_pdf,
)


def extract_pages_to_pdf(
    src_pdf_path: Path,
    from_page_0based: int,
    to_page_0based: int,
    dest_path: Path,
) -> bool:
    """
    Extracts a contiguous range of pages from src_pdf_path into dest_path.
    Uses temporary file for atomic write and validates before promoting.
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = dest_path.with_suffix(".tmp.pdf")

    try:
        src_doc = fitz.open(src_pdf_path)
        dst_doc = fitz.open()
        dst_doc.insert_pdf(src_doc, from_page=from_page_0based, to_page=to_page_0based)
        dst_doc.save(temp_path, garbage=4, deflate=True)
        dst_doc.close()
        src_doc.close()

        # Validate temporary file can be opened and has correct page count
        chk = fitz.open(temp_path)
        expected_pages = to_page_0based - from_page_0based + 1
        if len(chk) != expected_pages:
            chk.close()
            if temp_path.exists():
                temp_path.unlink()
            raise ValueError(f"Temporary PDF page count {len(chk)} != expected {expected_pages}")
        chk.close()

        # Atomically replace destination
        if dest_path.exists():
            dest_path.unlink()
        temp_path.rename(dest_path)
        return True
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        print(f"Error extracting {src_pdf_path} pages {from_page_0based}-{to_page_0based}: {e}")
        return False


def build_manifest_data(
    subject_id: str,
    display_name: str,
    textbook_title: str,
    textbook_part: str,
    standard: int,
    complete_pdf_rel: str,
    complete_pdf_path: Path,
    chapter_entries: list[dict[str, Any]],
) -> dict[str, Any]:
    doc = fitz.open(complete_pdf_path)
    source_sha = compute_sha256(complete_pdf_path)

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "subject": {
            "subject_id": subject_id,
            "display_name": display_name,
            "textbook_title": textbook_title,
            "textbook_part": textbook_part,
            "standard": standard,
            "complete_pdf": complete_pdf_rel,
            "source_sha256": source_sha,
            "source_page_count": len(doc),
            "source_file_size_bytes": complete_pdf_path.stat().st_size,
        },
        "chapters": chapter_entries,
    }


def process_subject(
    subject_key: str,
    base_dir: Path,
    dry_run: bool = False,
    validate_only: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    """
    Processes a single subject: History, Mathematics, or Environmental Studies.
    """
    subject_configs = {
        "history": {
            "subject_id": "history",
            "display_name": "History",
            "textbook_title": "Shivachhatrapati",
            "textbook_part": "Environmental Studies Part Two",
            "standard": 4,
            "subject_dir": base_dir / "History",
            "source_pdf": base_dir / "History" / "History.pdf",
            "chapters_dir": base_dir / "History" / "chapters",
            "metadata_dir": base_dir / "History" / "metadata",
            "chapter_defs": HISTORY_CHAPTERS,
            "special_evs_mode": False,
        },
        "maths": {
            "subject_id": "mathematics",
            "display_name": "Mathematics",
            "textbook_title": "Mathematics Part II",
            "textbook_part": "Standard X",
            "standard": 10,
            "subject_dir": base_dir / "Maths",
            "source_pdf": base_dir / "Maths" / "Mathematics.pdf",
            "chapters_dir": base_dir / "Maths" / "chapters",
            "metadata_dir": base_dir / "Maths" / "metadata",
            "chapter_defs": MATHEMATICS_CHAPTERS,
            "special_evs_mode": False,
        },
        "evs": {
            "subject_id": "evs",
            "display_name": "Environmental Studies",
            "textbook_title": "How We Came to Be",
            "textbook_part": "Environmental Studies Part Two",
            "standard": 5,
            "subject_dir": base_dir / "Environmental Studies",
            "source_pdf": base_dir / "Environmental Studies" / "EVS_Complete.pdf",
            "chapters_dir": base_dir / "Environmental Studies" / "chapters",
            "metadata_dir": base_dir / "Environmental Studies" / "metadata",
            "chapter_defs": EVS_CHAPTERS,
            "special_evs_mode": True,
        },
    }

    cfg = subject_configs[subject_key]
    print(f"\n=======================================================")
    print(f"Processing Subject: {cfg['display_name']} (Std {cfg['standard']})")
    print(f"Source PDF: {cfg['source_pdf']}")
    print(f"Modes: dry_run={dry_run}, validate_only={validate_only}, force={force}")
    print(f"=======================================================")

    chapters_dir: Path = cfg["chapters_dir"]
    metadata_dir: Path = cfg["metadata_dir"]
    chapters_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = metadata_dir / "chapter_manifest.json"
    chapter_records = []
    summary = {
        "subject": cfg["subject_id"],
        "total": len(cfg["chapter_defs"]),
        "generated": 0,
        "reused": 0,
        "repaired": 0,
        "validated": 0,
        "failed": 0,
    }

    for ch_def in cfg["chapter_defs"]:
        num = ch_def["chapter_number"]
        slug = ch_def["slug"]
        filename = f"chapter_{num:02d}_{slug}.pdf"
        dest_pdf = chapters_dir / filename
        rel_pdf_path = f"chapters/{filename}"

        p_start_1b = ch_def["pdf_page_start_1based"]
        p_end_1b = ch_def["pdf_page_end_1based"]
        b_start = ch_def["book_page_start"]
        b_end = ch_def["book_page_end"]
        expected_count = p_end_1b - p_start_1b + 1

        action_taken = "none"
        extraction_method = "direct_page_slice"
        legacy_path_rel = None

        if cfg["special_evs_mode"]:
            # Special EVS logic: inspect legacy file in subject folder
            legacy_filename = ch_def.get("legacy_filename")
            legacy_file = cfg["subject_dir"] / legacy_filename if legacy_filename else None
            legacy_path_rel = legacy_filename

            if legacy_file and legacy_file.exists():
                legacy_doc = fitz.open(legacy_file)
                legacy_len = len(legacy_doc)
                legacy_doc.close()

                if legacy_len == expected_count:
                    # Valid existing EVS PDF! Reuse it by ensuring standardized chapter exists
                    if not dest_pdf.exists() or force:
                        if not dry_run and not validate_only:
                            shutil.copy2(legacy_file, dest_pdf)
                            action_taken = "reused_copied_standardized"
                    else:
                        action_taken = "reused_existing"
                    summary["reused"] += 1
                else:
                    # Invalid legacy file (e.g. Chapter 10 has 11 pages instead of 8)
                    print(f"  [REPAIR] EVS Ch {num} legacy file has {legacy_len} pp (expected {expected_count}). Slicing from master...")
                    if not dry_run and not validate_only:
                        ok = extract_pages_to_pdf(
                            cfg["source_pdf"],
                            p_start_1b - 1,
                            p_end_1b - 1,
                            dest_pdf,
                        )
                        action_taken = "repaired_from_master" if ok else "repair_failed"
                    summary["repaired"] += 1
            else:
                # No legacy file, extract from master
                if not dry_run and not validate_only:
                    ok = extract_pages_to_pdf(
                        cfg["source_pdf"],
                        p_start_1b - 1,
                        p_end_1b - 1,
                        dest_pdf,
                    )
                    action_taken = "generated_from_master" if ok else "failed"
                summary["generated"] += 1
        else:
            # Standard subject: History or Mathematics
            needs_gen = not dest_pdf.exists() or force
            if needs_gen and not dry_run and not validate_only:
                ok = extract_pages_to_pdf(
                    cfg["source_pdf"],
                    p_start_1b - 1,
                    p_end_1b - 1,
                    dest_pdf,
                )
                action_taken = "generated" if ok else "failed"
                summary["generated"] += 1
            elif dest_pdf.exists():
                action_taken = "already_exists"
                summary["reused"] += 1

        # Validation check
        if dest_pdf.exists():
            val = validate_single_chapter_pdf(
                dest_pdf,
                cfg["source_pdf"],
                ch_def,
                verbose=True,
            )
            ch_sha = val["sha256"]
            ch_pages = val["page_count"]
            validation_status = "verified" if val["is_valid"] else "invalid"
            if val["is_valid"]:
                summary["validated"] += 1
            else:
                summary["failed"] += 1
            warnings = val["warnings"]
            errors = val["errors"]
        else:
            ch_sha = None
            ch_pages = None
            validation_status = "dry_run" if dry_run else "missing"
            warnings = []
            errors = ["PDF not created (dry-run or generation failed)"]
            if not dry_run:
                summary["failed"] += 1

        record = {
            "chapter_id": f"{cfg['subject_id']}_chapter_{num:02d}",
            "chapter_number": num,
            "title": ch_def["title"],
            "slug": slug,
            "pdf_path": rel_pdf_path,
            "legacy_pdf_path": legacy_path_rel,
            "source_pdf": cfg["source_pdf"].name,
            "source_pdf_page_start_1based": p_start_1b,
            "source_pdf_page_end_1based": p_end_1b,
            "printed_book_page_start": b_start,
            "printed_book_page_end": b_end,
            "chapter_pdf_page_count": ch_pages,
            "sha256": ch_sha,
            "action_taken": action_taken,
            "boundary_status": "verified",
            "validation_status": validation_status,
            "extraction_method": extraction_method,
            "warnings": warnings,
            "errors": errors,
        }
        chapter_records.append(record)

    # Build and write manifest
    manifest_data = build_manifest_data(
        subject_id=cfg["subject_id"],
        display_name=cfg["display_name"],
        textbook_title=cfg["textbook_title"],
        textbook_part=cfg["textbook_part"],
        standard=cfg["standard"],
        complete_pdf_rel=cfg["source_pdf"].name,
        complete_pdf_path=cfg["source_pdf"],
        chapter_entries=chapter_records,
    )

    if not dry_run:
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2, ensure_ascii=False)
        print(f"\nWrote manifest: {manifest_path} ({len(chapter_records)} chapters)")

    return {
        "config": cfg,
        "summary": summary,
        "manifest_path": str(manifest_path),
        "manifest_data": manifest_data,
    }


def main():
    parser = argparse.ArgumentParser(description="Segment textbooks and generate manifests.")
    parser.add_argument(
        "--subject",
        choices=["all", "history", "maths", "evs"],
        default="all",
        help="Subject to process",
    )
    parser.add_argument("--dry-run", action="store_true", help="Report planned actions without writing")
    parser.add_argument("--validate-only", action="store_true", help="Validate existing files only")
    parser.add_argument("--force", action="store_true", help="Force regeneration of chapter PDFs")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent.parent.parent

    subjects_to_run = (
        ["history", "maths", "evs"] if args.subject == "all" else [args.subject]
    )

    all_results = {}
    for sub in subjects_to_run:
        res = process_subject(
            sub,
            base_dir,
            dry_run=args.dry_run,
            validate_only=args.validate_only,
            force=args.force,
        )
        all_results[sub] = res

    print("\n=======================================================")
    print("FINAL SEGMENTATION & VALIDATION SUMMARY")
    print("=======================================================")
    for sub, res in all_results.items():
        s = res["summary"]
        print(
            f"{res['config']['display_name']}: "
            f"{s['validated']}/{s['total']} verified "
            f"(Gen: {s['generated']}, Reused: {s['reused']}, Repaired: {s['repaired']}, Failed: {s['failed']})"
        )


if __name__ == "__main__":
    main()
