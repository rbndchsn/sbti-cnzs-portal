# Approved Answer Portal

A free, static knowledge portal built on Governed Answer Retrieval (GAR): approved answers only, no live model at query time.

This project publishes a searchable webpage from a spreadsheet of reviewed Q&A. It is designed for official company knowledge, standards guidance, internal onboarding, SOPs, policy documents, and public FAQs.

The public site does **not** generate live AI answers. It suggests approved questions and waits for the user to select the intended question.

## Core Idea

```text
Google Sheet
↓
SMEs add or edit Q&A
↓
Committee or owner marks rows as approved
↓
Python script converts approved rows to qa.json
↓
Static website reads qa.json
↓
User searches, selects a suggested approved question, and sees the vetted answer
```

## Why This Exists

A live RAG chatbot may retrieve only a small top-k slice of the corpus and then generate an incomplete or overconfident answer. This portal uses a different model, Governed Answer Retrieval (GAR): AI drafts and quality-checks every answer up front, a human expert approves it, and at query time the site only retrieves approved answers, never generating. RAG generates at query time and hopes it is right; GAR approves the answer before the user ever asks. The trust model:

```text
AI may help draft and QA/QC content privately.
Humans approve the answer.
The public site only serves approved answers.
```

## Folder Architecture

```text
approved-answer-portal/
├── README.md
├── docs/
│   ├── ARCHITECTURE.md
│   ├── PORTAL_WRITE_CAPTURE_SPEC.md
│   └── SEARCH_OPTIONS.md
├── public/
│   ├── index.html
│   ├── assets/
│   │   ├── css/
│   │   │   └── styles.css
│   │   └── js/
│   │       └── app.js
│   └── data/
│       └── qa.json
├── templates/
│   └── qa_template.csv
└── tools/
    ├── csv_to_json.py
    ├── merge_csvs.py
    └── validate_qa.py
```

## Run It Locally (Preview)

You must view the site through a **local web server**. Opening `index.html` directly (double-click, or `file://`) leaves the page blank, because the browser blocks loading `data/qa.json` over `file://`.

### Option A: Terminal (works everywhere)

From the project root:

```bash
cd public
python3 -m http.server 8000
```

Then open `http://localhost:8000`. Stop the server with `Ctrl+C`.

### Option B: VS Code Live Server extension (no terminal)

1. Install the **Live Server** extension (publisher: Ritwick Dey).
2. In the Explorer, right-click `public/index.html` → **Open with Live Server**.
3. Your browser opens automatically (typically `http://127.0.0.1:5500/public/`).

Either way you are running a local server — that is the part that makes `data/qa.json` load. Publishing to GitHub Pages (below) replaces this with GitHub's own server, so end users never run anything.

## How Search Works in This Version

This version uses conservative keyword scoring.

When a user asks a question, the site:

1. Normalizes the text.
2. Removes common stop words.
3. Searches approved questions, alternate questions, tags, source, source section, and the answer text (answer matches rank below question, alternate, and tag matches).
4. Shows likely matching approved questions.
5. Waits for the user to select one.
6. Displays the vetted answer.

The site is intentionally designed **not** to auto-answer from a guessed match.

Possible outcomes:

```text
Strong match:
"Did you mean one of these approved questions?"

Weak match:
"Possible related approved questions"

No match:
"No approved question found. Try reformulating or browsing tags."
```

## Edit the Knowledge Base

Editing happens in **Google Sheets**, which is the single source of truth. The spreadsheet handles comma/newline escaping for you, so you never hand-edit raw CSV.

1. Import your candidate CSV(s) into Google Sheets, one tab each. The factory's per-document CSVs live in `content_factory/staging/`; `templates/qa_template.csv` is the blank schema reference.
2. Let SMEs add questions and answers.
3. Let the committee or owner mark approved rows with `status = approved`.
4. Export each reviewed tab as CSV (File → Download → Comma-separated values) and save it over its per-document file in `content_factory/staging/`.
5. Merge the per-document CSVs into one master, publish, and validate.

**Option A — one script (recommended):**

Open `tools/publish.py` in VS Code and click the Run button for production (approved rows only), or run from the terminal for local preview:

```bash
# Production: approved rows only (same as clicking Run in VS Code)
python3 tools/publish.py

# Local preview: all rows including draft
python3 tools/publish.py --drafts
```

`publish.py` runs all three steps in sequence: merge, convert, validate. It stops and reports the error if any step fails.

**Option B — step by step:**

```bash
python3 tools/merge_csvs.py \
  --input-dir content_factory/staging \
  --output content_factory/staging/qa_master.csv

# Production (approved rows only):
python3 tools/csv_to_json.py \
  --input content_factory/staging/qa_master.csv \
  --output public/data/qa.json

# Local preview (all rows including draft):
python3 tools/csv_to_json.py \
  --input content_factory/staging/qa_master.csv \
  --output public/data/qa.json \
  --include-drafts

python3 tools/validate_qa.py --input public/data/qa.json
```

`merge_csvs.py` combines every `*_qa.csv` in `content_factory/staging/` into `qa_master.csv` and fails on any duplicate `id`. `csv_to_json.py` publishes only `status = approved` rows by default; add `--include-drafts` for local preview. `qa_template.csv` is never overwritten.

> **Important:** always run the approved-only pipeline before pushing to GitHub Pages. The `--drafts` flag is for local preview only — it serves unreviewed content.

The scripts use only the Python standard library — no `pip install` step.

> **The Sheet does not auto-update from the CSVs; importing is manual.** Google Sheets will not
> sync a candidate CSV sitting on disk. To load one (the first time, or each new candidate), use
> **File → Import → Upload**, set the import location to **Insert new sheet(s)**, and **uncheck
> "Convert text to numbers, dates, and formulas"**. Each CSV then lands as its own tab. If that
> box stays checked, the import corrupts data: numeric-looking IDs lose leading zeros, `version`
> values like `1.0` collapse to `1`, and dates get reformatted. Uncheck it on every import.

## Approving a Row

Publishing is controlled by exactly one column: `status`. `tools/csv_to_json.py` exports a row only when its `status` is `approved` (case-insensitive). Every other value (`draft`, `under_review`, `archived`, `superseded`, or blank) is withheld, and nothing else in the row changes that.

To approve a row, in the Google Sheet:

1. Read the answer and confirm it is correct.
2. Set `status` to `approved`. That alone makes the row publishable.

The remaining review columns are optional and exist for your own audit trail. The converter copies `owner`, `reviewer`, `last_reviewed`, and `version` into `qa.json` verbatim but never reads them to decide anything. `version` is free text: any value works (`0.1`, `1.0`, `2.3`, or blank), and the pipeline does not interpret or enforce it, so a version scheme is a team choice, not a technical requirement.

One more rule the converter enforces: a row is skipped if `id`, `question`, or `answer` is empty, whatever its status.

## Spreadsheet Columns

| Column | Purpose |
|---|---|
| `id` | Unique answer ID, such as `q001` |
| `question` | Canonical approved question |
| `answer` | Approved answer shown to users |
| `alternate_questions` | Semicolon-separated alternate phrasings |
| `tags` | Semicolon-separated topic tags |
| `source` | Source document or policy name |
| `source_section` | Section, page, clause, or heading |
| `status` | `draft`, `under_review`, `approved`, `archived`, or `superseded` |
| `owner` | SME or team owner |
| `reviewer` | Reviewer or approval committee |
| `last_reviewed` | Review date |
| `version` | Answer version. Free text; copied to `qa.json` but not read by the converter |
| `notes` | Internal notes; not published to JSON |

Only rows with `status = approved` are published by default.

## Publishing on GitHub Pages

1. Create a GitHub repo.
2. Upload the project files.
3. In GitHub, go to **Settings → Pages**.
4. Set source to your branch and folder `/public`.
5. GitHub will give you a public URL.

## Search Upgrade Options

### Option 1: Current Version — Conservative Keyword Search

```text
User question
↓
Keyword/token scoring in JavaScript
↓
Suggested approved questions
↓
User selects one
↓
Approved answer appears
```

Best for:

- Maximum transparency
- No live AI
- No browser model loading
- No backend
- Free GitHub Pages hosting

Risk profile: lowest. The system only matches known words and approved alternate phrasings.

### Option 2: Browser Embeddings — Static Semantic Search

```text
qa.json contains precomputed embeddings
↓
User asks question
↓
Browser loads a small embedding model
↓
Browser embeds the user question
↓
JavaScript compares vectors
↓
Suggested approved questions appear
```

This can still run on GitHub Pages. It may use a browser library such as Transformers.js.

Benefits:

- Better at matching different wording
- Still no backend
- Still no API key
- Still compatible with static hosting

Risks/tradeoffs:

- First load is slower
- Older phones may struggle
- The embedding model introduces semantic interpretation
- Terms that are similar in ordinary language may not be equivalent in a standard, policy, or legal context

Use this only if keyword search plus alternate questions is not enough.

### Option 3: Backend Embedding API — More Powerful, More Infrastructure

```text
User asks question
↓
Website sends question to backend
↓
Backend creates embedding or runs search
↓
Backend returns suggested approved questions
↓
Website displays matches
```

Possible backends:

- FastAPI
- Supabase Edge Functions
- Firebase Functions
- Cloudflare Workers
- AWS Lambda
- Render / Railway / Fly.io

Benefits:

- Faster client experience
- Central logging
- Easier protected admin features
- Better semantic models
- Can add authentication and analytics

Risks/tradeoffs:

- No longer pure GitHub Pages
- More IT/security review
- More hosting complexity
- Possible cost
- More things can break

Use this only if you need centralized logging, protected admin workflows, or stronger search than static hosting can provide.

## Recommended Operating Model

```text
Private AI Factory:
documents → AI draft Q&A → AI QA/QC → SME/committee review → Google Sheet

Public Knowledge Portal:
approved rows → qa.json → GitHub Pages
```

The public product is simple. The private workflow can use AI heavily.

## Visitor Contributions (Planned)

The live site is read-only today. A planned feature lets visitors contribute without weakening the trust model:

- Report a wrong answer: a button on each answer card sends the answer's id and an optional comment to a private feedback inbox.
- Propose a question and answer: a short form sends a suggested question and answer to a private proposals inbox.

Neither one publishes automatically. Both land in inbox tabs in the same Google Sheet you already review, where you triage them into candidate rows, approve the good ones, and publish through the normal pipeline. A captured item reaches the public site only after a human approves it.

How it works, and why this way. A static site reads public files for free, but writing from the browser needs something that holds a secret, and there is no tokenless write to GitHub. Pasting a token into the page is not durable on the free plan, because GitHub Pages requires a public repo and GitHub automatically revokes any token it finds in a public repo. The receiver for this project is therefore a small Google Apps Script web app that appends submissions to the review Sheet: free, no Cloudflare, no token to leak or rotate, and the data lands where you already work. A pasted token writing straight to GitHub is kept only for throwaway demos. The full design is in `docs/PORTAL_WRITE_CAPTURE_SPEC.md`.

## Important Design Principle

The portal should not pretend to know what the user meant.

It should say:

```text
Did you mean one of these approved questions?
```

or:

```text
No approved question found. Try reformulating or browsing tags.
```

That is the trust advantage.
