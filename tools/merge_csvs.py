#!/usr/bin/env python3
"""
Merge the per-document candidate CSVs into one master CSV for publishing.

Reads every `*_qa.csv` in the input directory (default: content_factory/staging), checks they
all share the exact 13-column portal schema, concatenates their rows under a single header,
fails on any duplicate `id`, and writes one master CSV (default:
content_factory/staging/qa_master.csv, UTF-8 BOM, CRLF).

It is status-agnostic: every row (draft and approved) is carried over unchanged. Approved-only
filtering happens later, in csv_to_json.py. The master qa_master.csv is excluded from its own
inputs, so re-running is safe.

Pipeline:
  *_qa.csv  ->  merge_csvs.py  ->  qa_master.csv  ->  csv_to_json.py  ->  public/data/qa.json

Usage:
  python3 tools/merge_csvs.py
  python3 tools/merge_csvs.py --input-dir content_factory/staging \
      --output content_factory/staging/qa_master.csv
"""
import argparse
import csv
import sys
from pathlib import Path

SCHEMA = [
    "id", "question", "answer", "alternate_questions", "tags", "source",
    "source_section", "status", "owner", "reviewer", "last_reviewed", "version", "notes",
]

REPO = Path(__file__).resolve().parent.parent


def main() -> None:
    ap = argparse.ArgumentParser(description="Merge per-document *_qa.csv into one master CSV.")
    ap.add_argument("--input-dir", default=str(REPO / "content_factory" / "staging"),
                    help="Directory to scan (default: content_factory/staging)")
    ap.add_argument("--output", default=str(REPO / "content_factory" / "staging" / "qa_master.csv"),
                    help="Master CSV to write (default: content_factory/staging/qa_master.csv)")
    ap.add_argument("--pattern", default="*_qa.csv", help="Glob for input files (default: *_qa.csv)")
    args = ap.parse_args()

    in_dir = Path(args.input_dir)
    out_path = Path(args.output)
    # Fixed processing order — determines display order in the portal.
    # Files not listed here are appended alphabetically after the named ones.
    ORDER = [
        "sbti_cnzs_v2_faq_qa.csv",
        "sbti_cnzs_v2_key_questions_qa.csv",
        "sbti_cnzs_v2_qa.csv",
        "sbti_cnzs_v2_scope2_qa.csv",
        "sbti_cnzs_v2_main_changes_qa.csv",
        "sbti_cnzs_v2_continuing_use_qa.csv",
    ]
    all_files = {p.name: p for p in in_dir.glob(args.pattern) if p.resolve() != out_path.resolve()}
    ordered = [all_files[n] for n in ORDER if n in all_files]
    remaining = sorted(p for name, p in all_files.items() if name not in ORDER)
    files = ordered + remaining
    if not files:
        sys.exit(f"merge_csvs: no files matching {args.pattern!r} in {in_dir}")

    rows: list[dict] = []
    id_source: dict[str, str] = {}     # id -> first file it appeared in
    dups: list[tuple] = []             # (id, this_file, prior_file)
    schema_errors: list[tuple] = []
    per_file: list[tuple] = []

    for fp in files:
        with fp.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames != SCHEMA:
                schema_errors.append((fp.name, reader.fieldnames))
                continue
            n = 0
            for row in reader:
                rid = (row.get("id") or "").strip()
                if rid:
                    if rid in id_source:
                        dups.append((rid, fp.name, id_source[rid]))
                    else:
                        id_source[rid] = fp.name
                rows.append(row)
                n += 1
            per_file.append((fp.name, n))

    if schema_errors:
        print("merge_csvs: schema mismatch (expected the 13-column portal header):")
        for name, hdr in schema_errors:
            print(f"  {name}: {hdr}")
        sys.exit(1)

    if dups:
        print("merge_csvs: duplicate id values across files (fix before publishing):")
        for rid, here, prior in dups:
            print(f"  {rid}: in {here} and {prior}")
        sys.exit(1)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SCHEMA, quoting=csv.QUOTE_MINIMAL, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    print("merge_csvs: merged")
    for name, n in per_file:
        print(f"  {name}: {n} rows")
    print(f"  -> {out_path}  ({len(rows)} rows from {len(files)} files, all ids unique)")


if __name__ == "__main__":
    main()
