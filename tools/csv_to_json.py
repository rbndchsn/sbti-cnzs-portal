#!/usr/bin/env python3
"""
Convert approved Q&A rows from CSV to public/data/qa.json.

Usage:
  python3 tools/csv_to_json.py --input content_factory/staging/qa_master.csv --output public/data/qa.json
"""

import argparse
import csv
import json
from pathlib import Path


PUBLISHED_FIELDS = [
    "id", "question", "answer", "alternate_questions", "tags", "source",
    "source_section", "status", "owner", "reviewer", "last_reviewed", "version"
]


def split_semicolon(value: str) -> list[str]:
    """Split on semicolon or pipe — handles both separator conventions across CSVs."""
    v = value or ""
    sep = "|" if "|" in v else ";"
    return [x.strip() for x in v.split(sep) if x.strip()]


def convert_row(row: dict) -> dict:
    return {
        "id": row.get("id", "").strip(),
        "question": row.get("question", "").strip(),
        "answer": row.get("answer", "").strip(),
        "alternate_questions": split_semicolon(row.get("alternate_questions", "")),
        "tags": split_semicolon(row.get("tags", "")),
        "source": row.get("source", "").strip(),
        "source_section": row.get("source_section", "").strip(),
        "status": row.get("status", "").strip().lower(),
        "owner": row.get("owner", "").strip(),
        "reviewer": row.get("reviewer", "").strip(),
        "last_reviewed": row.get("last_reviewed", "").strip(),
        "version": row.get("version", "").strip(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Input CSV path")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument("--include-drafts", action="store_true", help="Include non-approved rows")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    with input_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        items = []
        for row in reader:
            status = row.get("status", "").strip().lower()
            if not args.include_drafts and status != "approved":
                continue
            item = convert_row(row)
            if not item["id"] or not item["question"] or not item["answer"]:
                continue
            items.append(item)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(items)} approved Q&A records to {output_path}")


if __name__ == "__main__":
    main()
