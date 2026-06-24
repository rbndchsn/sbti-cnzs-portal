# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A free, static "approved-answer" knowledge portal. Reviewed Q&A lives in a spreadsheet; a Python script exports only `status = approved` rows to `public/data/qa.json`; a dependency-free static site reads that JSON. There is **no backend and no build step** — the published artifact is just the contents of `public/`, hostable on GitHub Pages.

## Core design principle (do not break)

The portal is an *approved-question finder*, not a chatbot. It must **never auto-answer** from a guessed match. It scores the user's query against approved questions, presents ranked suggestions ("Did you mean one of these?"), and only shows a vetted answer after the user explicitly selects a question. This avoids collapsing terms that differ in a formal standard/policy/legal context. Preserve this behavior when editing search/UI logic.

## Commands

Serve the site locally — **required** for any preview. Opening `index.html` via `file://` leaves the page blank because the browser blocks the `fetch` of `qa.json` over `file://`. Two ways:

```bash
cd public && python3 -m http.server 8000   # then open http://localhost:8000; Ctrl+C to stop
```

In VS Code you can instead use the **Live Server** extension (Ritwick Dey): right-click `public/index.html` → "Open with Live Server" (serves at ~`http://127.0.0.1:5500/public/`). Both approaches just run a local HTTP server; that is the part that makes `qa.json` load.

Merge the reviewed per-document CSVs, regenerate `public/data/qa.json`, then validate (all three scripts use only the Python stdlib, no install step):

```bash
python3 tools/merge_csvs.py
python3 tools/csv_to_json.py --input content_factory/staging/qa_master.csv --output public/data/qa.json
python3 tools/validate_qa.py --input public/data/qa.json
```

`csv_to_json.py` publishes only `status = approved` rows by default; pass `--include-drafts` to include everything. `validate_qa.py` checks for missing `id`/`question`/`answer` and duplicate IDs, and exits non-zero on failure. There is no automated test suite or linter.

## Architecture

Data flows one direction: **Google Sheet → per-document CSV exports → `merge_csvs.py` → `qa_master.csv` → `csv_to_json.py` → `qa.json` → browser**. Static hosting cannot write back to `qa.json`, which is why editing happens in the spreadsheet and publishing happens via the Python scripts. A planned visitor write path (see "Write path (planned)" below) captures input to a separate inbox only, never to `qa.json`. The Google Sheet is the source of truth. The per-document CSVs in `content_factory/staging/` are regenerated from their reviewed tabs and merged into `qa_master.csv`; `templates/qa_template.csv` is only the blank schema reference, not a data file. Do not hand-edit either as if it were the master copy.

- `tools/csv_to_json.py` defines the published record shape and filtering rules. The `notes` column is deliberately excluded from the published JSON (governance: internal notes stay private). List fields `alternate_questions` and `tags` are semicolon-split.
- `tools/merge_csvs.py` combines every `*_qa.csv` in `content_factory/staging/` into `qa_master.csv`, enforcing one shared 13-column header and unique `id`s. It is status-agnostic; `csv_to_json.py` does the approved-only filtering.
- `public/assets/js/app.js` is the whole client. Key pieces: `scoreItem()` (keyword/token scoring with weighted fields + coverage bonus), `itemSearchText()` (the fields the search covers: question, alternates, tags, source, section, and the answer body, with the answer weighted lowest), the thresholds `MIN_SUGGEST_SCORE` / `STRONG_MATCH_SCORE` / `MAX_RESULTS` at the top of the file (tune ranking here), `tokenize()` + `stopWords` (normalization), and `showAnswer()` (renders the selected answer). All output goes through `escapeHtml()` — keep it that way since `qa.json` content is injected via `innerHTML`.
- `qa.json` is an array of records; `id` must be unique. Required for display: `id`, `question`, `answer`. Optional: `alternate_questions`, `tags`, `source`, `source_section`, `owner`, `reviewer`, `last_reviewed`, `version`.

If you add a new published field, update it in **two** places to keep the pipeline consistent: `csv_to_json.py` and the relevant render/score functions in `app.js`.

## Write path (planned, not yet implemented)

The portal is read-only today. A planned write-capture feature adds two visitor actions, both inbound only: report a wrong answer (a button on each answer card) and propose a question and answer (a small modal).

Mechanism, and why it is not what a first guess suggests. A static page cannot write to GitHub without a component that holds a secret (there is no tokenless write), and an embedded token is not durable here because Pages on the free plan requires a public repo and GitHub secret scanning auto-revokes any token committed to a public repo. The decided receiver is therefore a Google Apps Script web app (`doPost`) that appends each submission to the existing review Google Sheet, in two inbox tabs (feedback and proposals). No Cloudflare, no GitHub token, no second repo. An embedded token writing straight to the Contents API is reserved for throwaway demos only.

Trust gate (do not break). The receiver writes only the Sheet inbox tabs. It never writes `qa.json`, and nothing is auto-promoted. Captured items are triaged by the owner into reviewed rows, approved by SMEs (`status = approved`), and published only through the existing `merge_csvs.py` then `csv_to_json.py` pipeline. The full strategy and reference code are in `docs/PORTAL_WRITE_CAPTURE_SPEC.md` (see its Project decision note, which overrides the Cloudflare examples for this project).

## Search upgrade context

The current keyword search is "Option 1" (most conservative). `docs/SEARCH_OPTIONS.md` and the README describe two heavier alternatives (browser embeddings via Transformers.js; a backend embedding API). These are documented future options, not implemented — don't assume embedding infrastructure exists.
