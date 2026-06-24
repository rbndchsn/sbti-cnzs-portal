#!/usr/bin/env bash
# publish.sh — merge CSVs and rebuild qa.json
#
# Usage (run from the approved-answer-portal/ root):
#
#   bash tools/publish.sh            → approved rows only  (production)
#   bash tools/publish.sh --drafts   → all rows including draft  (local preview)
#
# Both commands write public/data/qa.json and print a row count.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

MASTER="$ROOT/content_factory/staging/qa_master.csv"
OUTPUT="$ROOT/public/data/qa.json"

echo "=== Step 1: merge per-document CSVs ==="
python3 "$ROOT/tools/merge_csvs.py" \
  --input-dir "$ROOT/content_factory/staging" \
  --output "$MASTER"

echo ""
echo "=== Step 2: convert to qa.json ==="
if [ "$1" = "--drafts" ]; then
  echo "(including draft rows — local preview mode)"
  python3 "$ROOT/tools/csv_to_json.py" \
    --input "$MASTER" \
    --output "$OUTPUT" \
    --include-drafts
else
  echo "(approved rows only — production mode)"
  python3 "$ROOT/tools/csv_to_json.py" \
    --input "$MASTER" \
    --output "$OUTPUT"
fi

echo ""
echo "=== Step 3: validate ==="
python3 "$ROOT/tools/validate_qa.py" --input "$OUTPUT"

echo ""
echo "Done. qa.json is ready at: $OUTPUT"
