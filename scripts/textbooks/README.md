# Textbook Ingestion & Chapter Segmentation Pipeline

This directory provides a modular, reproducible, offline-first textbook ingestion and chapter segmentation pipeline for the Learning Hub application.

## Overview

The pipeline processes three complete textbooks:
1. **History (Standard IV):** *Shivachhatrapati* (`History/History.pdf`, 92 pages) $\rightarrow$ 18 lessons
2. **Mathematics (Standard X):** *Mathematics Part II* (`Maths/Mathematics.pdf`, 180 pages) $\rightarrow$ 7 chapters
3. **Environmental Studies (Standard V):** *How We Came to Be* (`Environmental Studies/EVS_Complete.pdf`, 66 pages) $\rightarrow$ 10 lessons

## File Architecture

```text
scripts/textbooks/
├── discover_textbooks.py            # Textbook inspection, page counts, SHA256, and disk space
├── inspect_pdf.py                   # Low-level PDF bookmarks, text search, and page dumping
├── extract_chapter_boundaries.py    # Canonical boundary definitions and start/end heading validation
├── segment_textbook.py              # Lossless PyMuPDF page slicing and atomic manifest generation
├── validate_chapter_pdfs.py         # Structural, page-count, and content verification
├── run_textbook_ingestion.py        # Master pipeline runner and report generator
└── README.md                        # Documentation and command reference
```

## Prerequisites

- Python 3.10+ (tested on Python 3.12)
- `PyMuPDF` (`fitz`) installed in `.venv`
- Windows PowerShell or Bash

## Usage Commands

### 1. Discovery and Inventory
Inspect master PDFs, page counts, file sizes, SHA-256 checksums, and environment resources:
```powershell
.\.venv\Scripts\python.exe -m scripts.textbooks.discover_textbooks
```

### 2. Verify Chapter Boundaries
Verify printed book page to physical PDF page mappings against opening and closing headings:
```powershell
.\.venv\Scripts\python.exe -m scripts.textbooks.extract_chapter_boundaries
```

### 3. Validate Existing Chapter PDFs
Validate generated and legacy chapter PDFs without writing any files:
```powershell
.\.venv\Scripts\python.exe -m scripts.textbooks.segment_textbook --validate-only
```

### 4. Dry Run
Preview what the segmentation engine will do without creating or modifying files:
```powershell
.\.venv\Scripts\python.exe -m scripts.textbooks.segment_textbook --dry-run
```

### 5. Run Full Ingestion & Report Generation
Execute atomic page extraction, validate all chapter PDFs, write chapter manifests, and generate `reports/TEXTBOOK_INGESTION_REPORT.md`:
```powershell
.\.venv\Scripts\python.exe -m scripts.textbooks.run_textbook_ingestion
```

### 6. Subject-Specific Filtering & Force Rebuild
Regenerate a specific subject:
```powershell
# Slices only Mathematics and updates Maths/metadata/chapter_manifest.json
.\.venv\Scripts\python.exe -m scripts.textbooks.segment_textbook --subject maths --force
```

## Manifest Schema

Each subject manifest (`<Subject>/metadata/chapter_manifest.json`) follows a structured schema:
- `subject`: `subject_id`, `display_name`, `textbook_title`, `standard`, `source_sha256`, `source_page_count`
- `chapters`: list of chapter objects:
  - `chapter_id`: stable machine identifier (e.g. `history_chapter_01`)
  - `chapter_number`: integer (1-indexed)
  - `title`: official printed title
  - `pdf_path`: path relative to subject folder (`chapters/chapter_01_*.pdf`)
  - `source_pdf`: master textbook filename
  - `source_pdf_page_start_1based` & `source_pdf_page_end_1based`: 1-based physical PDF pages
  - `printed_book_page_start` & `printed_book_page_end`: 1-based printed page numbers
  - `chapter_pdf_page_count`: number of pages in chapter PDF
  - `sha256`: SHA-256 checksum of generated chapter PDF
  - `validation_status`: `"verified"`
