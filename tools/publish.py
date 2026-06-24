"""
publish.py — merge CSVs and rebuild qa.json

Run from anywhere; the script locates itself and finds the project root.

Usage:
    python3 tools/publish.py            # approved rows only  (production)
    python3 tools/publish.py --drafts   # all rows including draft  (local preview)

Steps:
    1. merge_csvs.py   — combines all staging/*_qa.csv into qa_master.csv
    2. csv_to_json.py  — converts qa_master.csv to public/data/qa.json
    3. validate_qa.py  — checks qa.json for missing fields and duplicate IDs
"""

import sys
import subprocess
from pathlib import Path

# Locate project root relative to this script (tools/ → approved-answer-portal/)
ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
STAGING = ROOT / "content_factory" / "staging"
MASTER = STAGING / "qa_master.csv"
OUTPUT = ROOT / "public" / "data" / "qa.json"

include_drafts = "--drafts" in sys.argv


def run(label, cmd):
    print(f"\n=== {label} ===")
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print(f"\nFailed at: {label}. Fix the error above and re-run.")
        sys.exit(result.returncode)


# Step 1 — merge
run(
    "Step 1: merge per-document CSVs",
    [sys.executable, str(TOOLS / "merge_csvs.py"),
     "--input-dir", str(STAGING),
     "--output", str(MASTER)]
)

# Step 2 — convert
cmd = [sys.executable, str(TOOLS / "csv_to_json.py"),
       "--input", str(MASTER),
       "--output", str(OUTPUT)]
if include_drafts:
    cmd.append("--include-drafts")
    print("\n(including draft rows — local preview mode)")
else:
    print("\n(approved rows only — production mode)")

run("Step 2: convert to qa.json", cmd)

# Step 3 — validate
run(
    "Step 3: validate qa.json",
    [sys.executable, str(TOOLS / "validate_qa.py"),
     "--input", str(OUTPUT)]
)

print(f"\nDone. qa.json is ready at:\n{OUTPUT}")
