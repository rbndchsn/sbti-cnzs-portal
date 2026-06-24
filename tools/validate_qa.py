#!/usr/bin/env python3
"""
Validate public/data/qa.json for duplicate IDs and missing required fields.

Usage:
  python3 tools/validate_qa.py --input public/data/qa.json
"""

import argparse
import json
from pathlib import Path


REQUIRED = ["id", "question", "answer"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    args = parser.parse_args()

    path = Path(args.input)
    data = json.loads(path.read_text(encoding="utf-8"))

    ids = set()
    errors = []

    for idx, item in enumerate(data, start=1):
        for field in REQUIRED:
            if not str(item.get(field, "")).strip():
                errors.append(f"Row {idx}: missing {field}")
        item_id = item.get("id")
        if item_id in ids:
            errors.append(f"Duplicate id: {item_id}")
        ids.add(item_id)

    if errors:
        print("Validation failed:")
        for err in errors:
            print(f"- {err}")
        raise SystemExit(1)

    print(f"Validation passed: {len(data)} records checked.")


if __name__ == "__main__":
    main()
