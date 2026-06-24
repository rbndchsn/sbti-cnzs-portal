---
title: SBTi → Approved Answer Portal — Content Processing Plan
subtitle: Extraction roadmap, per-document strategy, and progress for the SBTi Corporate Net-Zero Standard V2.0 corpus
author: Robin
date: 2026-06-21
version: 0.5
status: living document
source_files: SBTi CNZS V2.0 corpus (Drive folder 1azmkmlokfCV8OQLJ1ZsCFFlR18AhiYLL)
---

# Purpose

This plan governs how the SBTi Corporate Net-Zero Standard V2.0 corpus is turned into
draft Q&A rows for the Approved Answer Portal (1). It records the operating model, the
source inventory, the extraction method, the per-document strategy, the ID namespaces,
the processing order, and a running progress log, so the work is reproducible and auditable
and so any session can pick it up without re-deriving decisions.

# Operating model

Two halves, deliberately separated (1):

- **Private AI Factory** — documents are extracted into draft Q&A. Answers are lifted
  verbatim from the source; questions, alternates, and tags are drafted. Output is a
  candidate CSV per source document. This is the `content_factory/` tree.
- **Public Portal** — the Google Sheet is the single source of truth. SMEs review draft
  rows, approve them, and only `status = approved` rows are exported to `public/data/qa.json`
  by `tools/csv_to_json.py` and served by GitHub Pages (2).

The hard rule: the machine never authors an answer and never approves a row. Everything the
Factory produces ships as `status = draft`; the converter skips drafts by default, so nothing
generated here can reach the public site until a human flips it.

# Extraction method (applies to every document)

1. **PDF text layer is authoritative.** Words come from the embedded text layer
   (character-exact), never OCR/vision, which can silently alter a word or a "shall".
   Vision is reserved for tables/figures, where structure — not wording — is the content.
2. **The cleaned `.md` is not trusted** for extraction. It is a lossy derivative that
   flattened bulleted "shall" lists and dropped more than half of the glossary; it is kept
   only as a coverage cross-check (3).
3. **Lossless reassembly.** Line wraps are rejoined; line-end hyphens are preserved so real
   compounds ("long-term", "third-party") stay intact; embedded bullet lists are preserved.
   Only whitespace is normalized.
4. **Provenance on every row.** `source` and `source_section` are populated so each answer
   is auditable back to its exact origin.
5. **Draft status.** Every generated row is `status = draft`, `version 0.1`, with a
   provenance note.

# Source inventory

All files live in Drive folder `1azmkmlokfCV8OQLJ1ZsCFFlR18AhiYLL`.

| Document                                                | Pages              | Archetype                    | Status         | Namespace |
| ------------------------------------------------------- | ------------------ | ---------------------------- | -------------- | --------- |
| Corporate Net-Zero Standard V2.0 — Key Terms (glossary) | 85–101 of standard | Two-column table             | Done: 147 rows | `kt-###`  |
| Corporate Net-Zero Standard V2.0 — Criteria             | standard body      | Shall + bullet lists         | Queued         | `c-###`   |
| Corporate Net-Zero Standard V2.0: Standard body, key questions | standard body (most of the document) | Interpretive prose, lists, tables | Queued (next); workflow to be designed | `kq-###` |
| Corporate Net-Zero Standard V2 — FAQs                   | 6                  | Native FAQ                   | Done: 12 rows  | `faq-###` |
| Understanding Scope 2 in the Updated CNZS V2.0          | 6                  | Structured explainer         | Done: 11 rows  | `s2-###`  |
| Continuing Use of V1.3.1 and Transition to V2           | 3                  | Structured explainer         | Queued (2nd)   | `tr-###`  |
| Main Changes Document                                   | 13                 | Borderless comparison layout | Queued (3rd)   | `mc-###`  |
| Mandatory Five-Year Review Guidance                     | 21                 | Structured guidance          | Queued (4th)   | `fyr-###` |
| From Ambition to Action — Actions & Market Instruments  | 7                  | Prose guidance               | Queued (5th)   | `ama-###` |
| Guide for Companies in the Transition to CNZS V2        | 23                 | Graphics-heavy visual guide  | Queued (6th)   | `gd-###`  |

# Per-document strategy

- **Glossary (done).** Two-column Term/Definition table reconstructed by geometry; verbatim
  definitions verified against the PDF. 147 rows, complete A–Z (the `.md` had only 28).
- **FAQ (done).** Native Q&A: SBTi's own question wording is the canonical `question`; answers
  verbatim with bullet hierarchy preserved; alternates hand-authored. 12 rows.
- **Criteria (queued).** The core requirements. Rule: one `shall` + its intact bullet list =
  one verbatim answer, at sub-criterion granularity (CNZS-C##, C#.#, recommendations R#.#).
  `source_section` carries the exact criterion number. Questions authored.
- **Standard body, key questions (next).** The interpretive pass over the standard's
  narrative (executive summary, intent and rationale, section introductions, the
  explanation surrounding the criteria). It is question-first, not answer-first: we do not
  walk the document grabbing paragraphs and then formulating a question to fit a
  low-interest passage, which produces boring Q&A. We start from the questions a
  practitioner actually asks and keep a passage only when it genuinely answers one. The
  most extensive pass (document length, embedded lists, tables), so the workflow is
  designed before extraction. Default answer policy, pending that design: verbatim spans
  (the machine never authors an answer); a question that resolves only across scattered
  passages is split into narrower ones or flagged for SME authoring.
- **Understanding Scope 2 / Continuing Use / Five-Year Review.** Structured explainers with
  bold headings. Map each heading/topic to one authored question; answer verbatim from the
  section body.
- **Main Changes Document.** High portal value ("what changed about X?"). Borderless layout
  (not a ruled table), so each topic must be paired with its old→new change by position;
  needs careful structure work.
- **From Ambition to Action.** Prose guidance; section-based authored questions.
- **Transition Guide.** Graphics-heavy (~180 words/page, diagrams carry meaning). Lowest
  text yield; diagrams would need vision. Overlaps heavily with Continuing Use, Main Changes,
  and FAQ Q5/Q6 — do last, possibly only for content not already covered.

# Processing order

Standard body key questions (next, workflow to be designed) → Continuing Use → Main
Changes → Five-Year Review → From Ambition to Action → Transition Guide. Scope 2 is done.
Criteria can be slotted in at any point and pairs naturally with the standard body pass,
since both are extracted from the standard itself.

# Deduplication policy

The transition topic is covered by at least four sources (FAQ, Continuing Use, Transition
Guide, Main Changes). For the portal, multiple approved answers may coexist, but to avoid
publishing three near-identical answers: IDs are namespaced by source; near-duplicate
questions across sources are flagged in `notes` for SMEs to pick one canonical answer.

# Schema contract

One row per answer; 13 columns, exact order (4):

`id, question, answer, alternate_questions, tags, source, source_section, status, owner,
reviewer, last_reviewed, version, notes`

`alternate_questions` and `tags` are semicolon-separated. File is UTF-8 with BOM, CRLF line
endings, matching the existing template and `csv_to_json.py`. `notes` is never published.
Each source document produces its own candidate CSV in `staging/`; none overwrites
`qa_template.csv`. Import each into the Sheet as a separate tab.

# Governance / review workflow

The review Google Sheet exists: **"SBTi Approved Answer Portal — QA"** (Luc's Drive). Each
candidate CSV is imported as its own tab named `<doc>_draft`. Live tabs: `glossary_draft`,
`faq_draft`, `scope2_draft`. The tab name is cosmetic; the converter reads an exported CSV, not
tab names, and row `id` namespaces (`kt-`, `faq-`, `s2-`) keep the corpora distinct.

1. Factory emits a candidate CSV (`status = draft`).
2. Import into the Sheet as a new `<doc>_draft` tab (File → Import → Upload → Insert new sheet;
   uncheck "convert text to numbers/dates" to protect IDs and `version`).
3. SMEs review answers, set `status = approved`, fill `owner` / `reviewer` / `last_reviewed`.
4. Export each reviewed tab back over its per-document CSV in `staging/`.
5. `tools/merge_csvs.py` combines the per-document CSVs into `staging/qa_master.csv`; `tools/csv_to_json.py` publishes only `approved` rows from it to `public/data/qa.json` (2).

# Visitor contribution channel (write-capture)

This is the last step in the plan, and it is deliberately deferred: the portal
already works as a read-only approved-answer finder, and more Q&A can be added
through the existing pipeline while it waits. The write-capture adds the portal's
first inbound channel, so visitors can flag a wrong answer or suggest content,
without weakening the trust gate.

Two features:

- Report a wrong answer: one button on each answer card appends a single record
  (id, question, source, optional comment, timestamp) to a feedback inbox.
- Propose a question and answer: a small two-field modal appends a record
  (proposed_question, proposed_answer, timestamp) to a proposals inbox.

Why the design is what it is. A static site reads public files for free, but any
write from an anonymous browser needs a component that holds a secret, because
GitHub has no tokenless write endpoint (5). A token pasted into the page is not
durable on the free plan: GitHub Pages requires a public repo (6), and GitHub
secret scanning automatically revokes any token committed to a public repo (7).
An embedded token writing straight to the Contents API is therefore acceptable
for a throwaway client demo only, never for the standing portal.

Decision (2026-06-21): the secret-holder for this project is Google, not
Cloudflare. A Google Apps Script web app (a doPost receiver deployed to run as the
owner and accept anonymous requests) takes each submission and appends a row to the
existing review Google Sheet, in two new inbox tabs (for example feedback_inbox and
proposed_inbox) (8). There is no GitHub token in the flow, because the write target
is the Sheet rather than a repo; there is no Cloudflare, no second repo, and nothing
to rotate or revoke. A zero-code fallback (two Google Forms feeding the same tabs)
is available if the script is ever undesirable.

Trust gate (unchanged). The inbox tabs are raw, unvetted input, never published
content. The owner triages them, copies useful items into reviewed candidate rows,
SMEs set status = approved, and only then does the existing merge_csvs.py then
csv_to_json.py pipeline publish to public/data/qa.json (2). The receiver writes only
the inbox tabs; it never writes qa.json, and there is no automatic promotion from
inbox to published answer. Every public answer stays human-approved and
source-traceable.

# Known issues and decisions

- **Review Sheet is live; import is manual.** The single source of truth is the Google Sheet
  "SBTi Approved Answer Portal — QA", with one `<doc>_draft` tab per candidate CSV
  (`glossary_draft`, `faq_draft`, `scope2_draft`). Candidate CSVs are written to
  `content_factory/staging/` and imported by hand, since the Drive connector's writes remain
  unreliable (reads work).
- **Multiline answers.** FAQ (and future explainer) answers contain bullet lists with real
  line breaks. The CSV and `qa.json` preserve them as `\n`; the portal front-end must render
  newlines (`white-space: pre-wrap`, `\n`→`<br>`, or Markdown) or bullets will collapse.
- **Long glossary terms.** The three "Default-delivered LCE" variants have long, clause-like
  headwords as defined in the standard; extraction is faithful, but their auto-generated
  "What is …?" questions should be reworded on review.

# Progress log

- 2026-06-20 — Glossary extracted: 147 verbatim rows (`kt-001`..`kt-147`), draft.
- 2026-06-20 — FAQ extracted: 12 verbatim rows (`faq-001`..`faq-012`), draft.
- 2026-06-20 — Companion corpus surveyed (6 documents); processing order set.
- 2026-06-20: Understanding Scope 2 extracted: 11 verbatim rows (`s2-001`..`s2-011`), draft. Heading-driven, geometry-based reassembly (gap and x-position) preserves paragraphs, bullets, and compound hyphens; all 11 answers verified as exact substrings of the PDF text layer. The "Raising the bar for scope 2 integrity" section is split into an overview plus its near / new / now sub-principles; `s2-010` (hourly matching) overlaps `faq-010` and is flagged for SME dedup.
- 2026-06-20: Review Google Sheet "SBTi Approved Answer Portal — QA" set up. Each candidate CSV imported as its own `<doc>_draft` tab: `glossary_draft`, `faq_draft`, `scope2_draft`. Scope 2 rows (`s2-001`..`s2-011`) loaded.
- 2026-06-20: Added `tools/merge_csvs.py` (publish pipeline). It combines all `staging/*_qa.csv` into `staging/qa_master.csv` (one 13-column header, fails on duplicate id, status-agnostic); `csv_to_json.py` then converts `qa_master.csv` to `qa.json` (approved-only). Verified end to end: 170 rows merged, 170 via `--include-drafts`, 0 approved-only, and the duplicate-id and bad-header guards both fail closed. README, CLAUDE.md, the `csv_to_json` docstring, and the governance steps updated to the merge flow; `qa_template.csv` stays the schema template and is never overwritten.
- 2026-06-21: Decided the write-capture strategy. Visitor submissions (report a wrong answer; propose a Q&A) will post to a Google Apps Script web app that appends rows to the review Sheet (feedback and proposals inbox tabs). No Cloudflare and no embedded token: free Pages requires a public repo and GitHub secret scanning auto-revokes any committed token, so an embedded token is demo-only (7). The inbox feeds the existing approve-then-publish pipeline; nothing auto-publishes. Scheduled as the last step. Reconciled the portal CLAUDE.md and README.md, the content_factory README, and added a Project decision note to `docs/PORTAL_WRITE_CAPTURE_SPEC.md` (which otherwise recommends a Cloudflare Worker).
- 2026-06-21: Added a fourth standard-derived pass, **Standard body, key questions** (`kq-###`), and moved it to next in the order. It is distinct from glossary (definitions), criteria (shall-statements), and the FAQ companion: an interpretive, question-first reading of the standard's narrative. Flagged as the most extensive pass (length, lists, tables); the workflow will be designed before extraction. Default answer policy pending that design: verbatim spans, machine never authors.

# End-of-session checklist (run after every document pass)

After completing a new candidate CSV, always do these steps before closing the session:

1. Run `python3 tools/publish.py --drafts` from the `approved-answer-portal/` root to merge all CSVs, rebuild `qa.json`, and validate. This makes the new rows immediately visible in the local preview.
2. Import the new CSV into the Google Sheet as a new `<doc>_draft` tab (File → Import → Upload → Insert new sheet; uncheck "Convert text to numbers, dates, and formulas").
3. Note the row count and namespace in the Progress log below.

When content is SME-approved and ready for production, run `python3 tools/publish.py` (no `--drafts`) and push `public/data/qa.json` to GitHub.

# Next steps

1. **Five-Year Review** (`fyr-###`): next in processing order.
2. **From Ambition to Action** (`ama-###`): after Five-Year Review.
3. **Transition Guide** (`gd-###`): after From Ambition to Action.
4. **Continuing Use** (`tr-###`): skipped ahead of Main Changes by Luc's choice; slot in when ready.
5. Run the **criteria** pass (`c-###`) on the standard when prioritized.
6. **Write-capture (last step).** Build the visitor contribution channel: two features post to a Google Apps Script web app that appends rows to the review Sheet (feedback and proposals inbox tabs). No Cloudflare and no embedded token. Deferred until the content passes are far enough along; the read-only portal is fully usable now.

# References

(1) Approved Answer Portal — `README.md`, "Why This Exists" and "Recommended Operating Model".
(2) Approved Answer Portal — `CLAUDE.md`, "Architecture"; `README.md`, "Edit the Knowledge Base".
(3) SBTi Corporate Net-Zero Standard V2.0 (June 2026) PDF vs. `..._cleanfinal.md` derivative.
(4) Approved Answer Portal — `templates/qa_template.csv` header; `tools/csv_to_json.py` `PUBLISHED_FIELDS`.
(5) GitHub REST API, repository contents and dispatch endpoints; writes require authentication: https://docs.github.com/en/rest/repos/repos
(6) GitHub Docs, GitHub's plans; Pages on the Free plan requires a public repo: https://docs.github.com/get-started/learning-about-github/githubs-products
(7) GitHub Docs, About secret scanning; automatic revocation of tokens leaked in public repositories: https://docs.github.com/code-security/secret-scanning/about-secret-scanning
(8) Google Apps Script, Web apps; doPost, deploy to execute as the owner, accessible to anyone: https://developers.google.com/apps-script/guides/web
