"""
Textbook Discovery and Inventory Module.
Discovers complete textbooks, calculates SHA-256 checksums, inspects page counts,
detects text searchability, checks disk space and environment dependencies.
"""
from __future__ import annotations
import os
import sys
import shutil
import hashlib
import json
from pathlib import Path
from typing import Any
import fitz  # PyMuPDF


def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def inspect_textbook(pdf_path: Path, subject_name: str, standard: int, title: str) -> dict[str, Any]:
    if not pdf_path.exists():
        return {
            "subject": subject_name,
            "exists": False,
            "path": str(pdf_path),
            "error": "File not found",
        }

    stat = pdf_path.stat()
    file_size = stat.st_size
    sha256_hash = compute_sha256(pdf_path)

    doc = fitz.open(pdf_path)
    page_count = len(doc)

    # Check searchability
    pages_with_text = 0
    sample_pages = min(20, page_count)
    for p in range(sample_pages):
        if len(doc[p].get_text().strip()) > 30:
            pages_with_text += 1

    searchable = pages_with_text > 0

    return {
        "subject": subject_name,
        "standard": standard,
        "title": title,
        "path": str(pdf_path),
        "relative_path": str(pdf_path.relative_to(pdf_path.parent.parent)),
        "exists": True,
        "file_size_bytes": file_size,
        "file_size_mb": round(file_size / (1024 * 1024), 2),
        "sha256": sha256_hash,
        "page_count": page_count,
        "is_encrypted": doc.is_encrypted,
        "sample_searchable_ratio": f"{pages_with_text}/{sample_pages}",
        "has_searchable_text": searchable,
    }


def discover_all_textbooks(base_dir: Path) -> dict[str, Any]:
    # Disk space
    disk = shutil.disk_usage(base_dir)
    free_gb = round(disk.free / (1024**3), 2)
    total_gb = round(disk.total / (1024**3), 2)

    # Dependencies
    deps = {
        "python_version": sys.version.split()[0],
        "pymupdf_version": fitz.__version__,
    }

    history_info = inspect_textbook(
        base_dir / "History" / "History.pdf",
        "History",
        4,
        "Shivachhatrapati (Environmental Studies Part Two)",
    )

    maths_info = inspect_textbook(
        base_dir / "Maths" / "Mathematics.pdf",
        "Mathematics",
        10,
        "Mathematics Part II (Standard X)",
    )

    evs_info = inspect_textbook(
        base_dir / "Environmental Studies" / "EVS_Complete.pdf",
        "Environmental Studies",
        5,
        "How We Came to Be (Environmental Studies Part Two)",
    )

    # Existing EVS chapter files count
    evs_dir = base_dir / "Environmental Studies"
    existing_evs_files = list(evs_dir.glob("Chapter *.pdf"))

    return {
        "environment": {
            "root_dir": str(base_dir),
            "free_disk_gb": free_gb,
            "total_disk_gb": total_gb,
            "dependencies": deps,
        },
        "textbooks": {
            "history": history_info,
            "mathematics": maths_info,
            "evs": evs_info,
        },
        "existing_evs_chapter_files_count": len(existing_evs_files),
        "existing_evs_chapter_files": [f.name for f in existing_evs_files],
    }


if __name__ == "__main__":
    base = Path(__file__).resolve().parent.parent.parent
    inv = discover_all_textbooks(base)
    print(json.dumps(inv, indent=2))
