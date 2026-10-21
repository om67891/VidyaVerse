"""
Validation utility for chapter-wise PDFs.
Performs structural validation, page count validation, and content validation
against the master complete textbook.
"""
from __future__ import annotations
import sys
import hashlib
from pathlib import Path
from typing import Optional
import fitz  # PyMuPDF

from scripts.textbooks.extract_chapter_boundaries import (
    HISTORY_CHAPTERS,
    MATHEMATICS_CHAPTERS,
    EVS_CHAPTERS,
)


def compute_sha256(filepath: Path) -> str:
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def validate_single_chapter_pdf(
    chapter_pdf_path: Path,
    master_pdf_path: Path,
    chapter_info: dict,
    verbose: bool = True,
) -> dict:
    """
    Validates a chapter PDF against its expected boundaries and master PDF content.
    """
    res = {
        "chapter_number": chapter_info["chapter_number"],
        "title": chapter_info["title"],
        "path": str(chapter_pdf_path),
        "exists": chapter_pdf_path.exists(),
        "is_valid": False,
        "page_count": 0,
        "expected_page_count": chapter_info["pdf_page_end_1based"] - chapter_info["pdf_page_start_1based"] + 1,
        "sha256": None,
        "file_size": 0,
        "errors": [],
        "warnings": [],
    }

    if not chapter_pdf_path.exists():
        res["errors"].append(f"File not found: {chapter_pdf_path}")
        return res

    res["file_size"] = chapter_pdf_path.stat().st_size
    res["sha256"] = compute_sha256(chapter_pdf_path)

    try:
        ch_doc = fitz.open(chapter_pdf_path)
    except Exception as e:
        res["errors"].append(f"Failed to open PDF: {e}")
        return res

    res["page_count"] = len(ch_doc)

    if res["page_count"] == 0:
        res["errors"].append("PDF is empty (0 pages).")
        return res

    if res["page_count"] != res["expected_page_count"]:
        res["errors"].append(
            f"Page count mismatch: got {res['page_count']}, expected {res['expected_page_count']}"
        )

    # Check text content on page 1
    p1_text = ch_doc[0].get_text().strip()
    if not p1_text:
        res["warnings"].append("Page 1 has no extractable text (may be image/scanned).")
    else:
        # Title check: at least partial title or chapter number should appear
        title_words = [w.lower() for w in chapter_info["title"].split() if len(w) > 3]
        matches = [w for w in title_words if w in p1_text.lower()]
        ch_num_str = str(chapter_info["chapter_number"])
        if not (matches or ch_num_str in p1_text):
            res["warnings"].append(
                f"Chapter title words {title_words} or number '{ch_num_str}' not clearly found on page 1."
            )

    # Compare with master PDF if provided
    if master_pdf_path and master_pdf_path.exists():
        try:
            master_doc = fitz.open(master_pdf_path)
            master_start = chapter_info["pdf_page_start_1based"] - 1
            master_p1_text = master_doc[master_start].get_text().strip()
            
            # If master has text, verify chapter page 1 has matching key content
            if master_p1_text and p1_text:
                overlap = len(set(master_p1_text.split()) & set(p1_text.split()))
                if overlap < 5:
                    res["warnings"].append(
                        f"Page 1 text differs substantially from master page {master_start + 1}."
                    )
        except Exception as e:
            res["warnings"].append(f"Could not cross-check with master PDF: {e}")

    res["is_valid"] = len(res["errors"]) == 0

    if verbose:
        status_tag = "[PASS]" if res["is_valid"] else "[FAIL]"
        print(
            f"  {status_tag} Ch {res['chapter_number']:02d}: {res['title'][:32]}... "
            f"({res['page_count']} pp, {res['file_size']:,} bytes)"
        )
        for err in res["errors"]:
            print(f"       ERROR: {err}")
        for w in res["warnings"]:
            print(f"       WARNING: {w}")

    return res


def inspect_existing_evs_chapters(evs_dir: Path, master_pdf_path: Path):
    """
    Inspects existing EVS PDFs in the Environmental Studies directory.
    Determines if they are valid or need repair/standardisation.
    """
    print(f"\n=======================================================")
    print(f"Inspecting existing EVS chapters in {evs_dir}")
    print(f"=======================================================")

    results = []
    for ch in EVS_CHAPTERS:
        legacy_name = ch.get("legacy_filename")
        legacy_path = evs_dir / legacy_name if legacy_name else None
        
        # Check if legacy file exists
        if legacy_path and legacy_path.exists():
            val = validate_single_chapter_pdf(legacy_path, master_pdf_path, ch, verbose=True)
            results.append((ch, legacy_path, val))
        else:
            print(f"  [MISSING] Ch {ch['chapter_number']:02d}: {ch['title']} (Expected: {legacy_name})")
            results.append((ch, None, {"is_valid": False, "errors": ["File missing"]}))

    valid_count = sum(1 for _, _, v in results if v.get("is_valid"))
    print(f"\nExisting EVS inspection result: {valid_count}/{len(EVS_CHAPTERS)} valid.")
    return results


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent.parent
    evs_dir = base_dir / "Environmental Studies"
    evs_master = evs_dir / "EVS_Complete.pdf"

    inspect_existing_evs_chapters(evs_dir, evs_master)
