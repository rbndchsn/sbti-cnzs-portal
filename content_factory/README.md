---
title: Content Factory — SBTi CNZS v2.0 Q&A Extraction
subtitle: Private extraction pipeline that drafts verbatim Q&A for the Approved Answer Portal
author: Robin
date: 2026-06-21
version: 0.2
status: draft
source_files: Corporate-Net-Zero-Standard-version-2.pdf
---

# Purpose

This folder is the **private AI Factory** described in the portal README (1): it turns a
source standard into draft Q&A rows for human review. It is deliberately separate from the
published product. GitHub Pages serves only `public/`, so nothing here is ever exposed to end
users. The deliverable that leaves this folder is a candidate CSV you import into the Google
Sheet (the single source of truth), where SMEs review and approve rows before they reach the
portal (2).

The governing constraint: **answers are lifted verbatim from the source; the machine never
authors an answer.** Questions, alternate phrasings, and tags are machine-drafted and ship as
`status = draft` for human approval. This is the disciplined form of the portal's own trust
model — AI may draft, only humans approve (1).

# Source of truth for extraction

The authoritative source is the **PDF**, not the Markdown. The cleaned `.md` derived from the
PDF is a lossy conversion: it flattened bulleted "shall" lists into repeated sentences and
silently dropped more than half of the glossary (its Key Terms ended at "P"; the PDF runs to
"W"). All extraction therefore reads the PDF text layer directly. The `.md` is retained only as
a cross-check for completeness, never as the extraction input.

The PDF is born-digital and tagged (Adobe InDesign), with a clean, character-exact embedded text
layer. Words are taken from that text layer (exact), never from OCR/vision, which could silently
alter a word or a "shall". Vision is reserved for tables and figures only, where structure — not
wording — is the content.

# Folder layout

```text
content_factory/
├── README.md                  ← this file
├── sources/                   ← authoritative source(s); PDF lives in the SBTi source folder
├── extraction/
│   ├── extract_glossary.py    ← PDF Key-Terms table → verbatim units (geometry-based)
│   └── build_csv.py           ← verbatim units → draft CSV in the portal schema
└── staging/
    ├── glossary_units.jsonl   ← intermediate: verbatim answers + auto source tags
    └── sbti_cnzs_v2_qa.csv    ← candidate, portal schema → import to the Google Sheet
```

# Pipeline

```text
PDF (authoritative)
  ↓  extract_glossary.py     reconstruct the two-column Key Terms table by geometry
glossary_units.jsonl         verbatim definitions + source / source_section
  ↓  build_csv.py            author questions / alternates / tags (status = draft)
sbti_cnzs_v2_qa.csv          13-column portal schema, status = draft
  ↓  (you) import to Google Sheet → SME review → status = approved
  ↓  tools/csv_to_json.py    (existing product pipeline) publishes approved rows only
public/data/qa.json
```

# How to re-run

From this folder, with the PDF available (adjust the path in `extract_glossary.py` if needed):

```bash
python3 extraction/extract_glossary.py     # writes staging/glossary_units.jsonl
python3 extraction/build_csv.py            # writes staging/sbti_cnzs_v2_qa.csv
```

Both use only `pdftotext`/PyMuPDF for reading and the Python standard library for the CSV. The
CSV is UTF-8 with BOM (`utf-8-sig`) and CRLF line endings to match the existing template and the
reader in `tools/csv_to_json.py`.

# Fidelity method (how "verbatim" is guaranteed)

- The Key Terms section is a two-column table (Term | Definition) on PDF pages 85–101. Columns
  share a font, so entries are reconstructed by x-position (term column vs definition column) and
  vertical-gap entry boundaries, not by guessing.
- Line wrapping is reassembled losslessly: a line-ending hyphen is preserved (so "long-term" and
  "third-party" stay intact, rather than collapsing to "longterm"/"thirdparty" the way naive
  de-hyphenation does). Only whitespace is normalized; no word is added, removed, or reordered.
- Embedded bullet lists inside a definition (e.g. "Net-zero target") are preserved.
- `source` and `source_section` are auto-populated for every row, so each answer is auditable
  back to its exact origin in the standard (3).

# Current output

- `staging/sbti_cnzs_v2_qa.csv`: **147 glossary rows**, all `status = draft`, IDs `kt-001`..`kt-147`.
- Verbatim answers; machine-drafted questions/alternates/tags pending review.

# Known items for SME review

- A few Key Terms have long, clause-like headwords as defined in the standard itself
  (the three "Default-delivered LCE" variants, one with a multi-line qualifier). Extraction is
  faithful, but the auto-generated "What is …?" question reads awkwardly for these and should be
  reworded on review. The full term is retained verbatim in `source_section` and as an alternate.
- Acronyms found in a definition (e.g. LCE) are added as alternate questions; confirm they are
  the intended short forms.

# Scope status

- [x] Glossary / Key Terms (this pass)
- [x] FAQ (companion doc): 12 rows, `faq-###`
- [x] Understanding Scope 2 (companion doc): 11 rows, `s2-###`
- [ ] Criteria (CNZS-C## / sub-criteria / recommendations) — next; the "shall + intact bullet
      list" grouping does the real work here, sourced the same way from the PDF.
- [ ] Narrative sections (Executive Summary, Intent blocks)
- [ ] Tables (Table 1, Table 3, Annex A.1) — table-aware / vision extraction

# New intake: visitor proposals (planned)

Beyond document extraction, the portal will gain a visitor "propose a question and
answer" feature. Those submissions land in a proposals inbox tab in the review Google
Sheet (4), alongside a feedback inbox for "report a wrong answer". They are an
additional, human-triaged source of candidate rows: they enter the same
draft-then-approve flow as extracted rows and never publish without approval. The
Factory's rule is unchanged: the machine never authors or approves an answer (1). The
receiver is a Google Apps Script web app writing to the Sheet, not Cloudflare and not
an embedded token; the full strategy is in the portal's
`docs/PORTAL_WRITE_CAPTURE_SPEC.md`.

# References

(1) Approved Answer Portal — `README.md`, "Why This Exists" and "Recommended Operating Model".
(2) Approved Answer Portal — `README.md`, "Edit the Knowledge Base" and "Spreadsheet Columns".
(3) SBTi Corporate Net-Zero Standard V2.0, June 2026 — Key Terms (pp. 85–101).
(4) Approved Answer Portal, `docs/PORTAL_WRITE_CAPTURE_SPEC.md`, "Project decision" (write-capture strategy).
