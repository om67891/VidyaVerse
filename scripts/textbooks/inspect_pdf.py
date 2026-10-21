"""
Utility to inspect PDF structure, text, bookmarks, and page content.
"""
import sys
import os
import hashlib
from pathlib import Path
import fitz  # PyMuPDF


def get_pdf_info(pdf_path: Path):
    if not pdf_path.exists():
        print(f"Error: {pdf_path} does not exist.")
        return None

    doc = fitz.open(pdf_path)
    file_size = pdf_path.stat().st_size
    with open(pdf_path, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()

    toc = doc.get_toc()

    info = {
        "path": str(pdf_path),
        "page_count": len(doc),
        "file_size": file_size,
        "sha256": file_hash,
        "toc_entries": len(toc),
        "toc": toc,
        "is_encrypted": doc.is_encrypted,
    }
    return info


def dump_pages(pdf_path: Path, start_1based: int, end_1based: int):
    doc = fitz.open(pdf_path)
    print(f"\n=== Dumping {pdf_path.name} (pages {start_1based} to {end_1based}) ===")
    for p in range(start_1based - 1, min(len(doc), end_1based)):
        page = doc[p]
        text = page.get_text()
        print(f"\n--- Physical Page {p + 1} (Length: {len(text)} chars) ---")
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for line in lines[:25]:
            print(f"  {line}")


def search_in_pdf(pdf_path: Path, query: str, max_pages: int = 30):
    doc = fitz.open(pdf_path)
    print(f"\n=== Searching '{query}' in {pdf_path.name} (first {max_pages} pages) ===")
    found = 0
    for p in range(min(len(doc), max_pages)):
        text = doc[p].get_text()
        if query.lower() in text.lower():
            found += 1
            print(f"\n[Found match on Physical Page {p + 1}]:")
            for line in text.split("\n"):
                if query.lower() in line.lower():
                    print(f"  >>> {line.strip()}")
    if found == 0:
        print(f"No match found for '{query}' in first {max_pages} pages.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python inspect_pdf.py <pdf_path> [dump start_page end_page | search query]")
        sys.exit(1)

    pdf = Path(sys.argv[1])
    info = get_pdf_info(pdf)
    if not info:
        sys.exit(1)

    print(f"PDF: {info['path']}")
    print(f"Pages: {info['page_count']}, Size: {info['file_size']:,} bytes, SHA256: {info['sha256']}")
    print(f"Bookmarks count: {info['toc_entries']}")

    if len(sys.argv) >= 5 and sys.argv[2] == "dump":
        dump_pages(pdf, int(sys.argv[3]), int(sys.argv[4]))
    elif len(sys.argv) >= 4 and sys.argv[2] == "search":
        search_in_pdf(pdf, sys.argv[3])
    else:
        # Default: print first 10 pages brief headers
        dump_pages(pdf, 1, min(12, info["page_count"]))
