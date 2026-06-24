#!/usr/bin/env python3
"""Build the draft candidate CSV (portal schema) from scope2_units.jsonl.

Answers are verbatim from the SBTi 'Understanding Scope 2' explainer (paragraph and bullet
structure preserved). Questions, alternate phrasings, and tags are authored for SME review.
status=draft, version=0.1. ID namespace: s2-###. No em dashes / double hyphens in any authored
field (house style). Output: staging/sbti_cnzs_v2_scope2_qa.csv (UTF-8 BOM, CRLF)."""
import json, csv, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IN   = os.path.join(ROOT, "staging", "scope2_units.jsonl")
OUT  = os.path.join(ROOT, "staging", "sbti_cnzs_v2_scope2_qa.csv")

HEADER = ["id", "question", "answer", "alternate_questions", "tags", "source",
          "source_section", "status", "owner", "reviewer", "last_reviewed", "version", "notes"]
SRC = "SBTi: Understanding Scope 2 in the Updated Corporate Net-Zero Standard V2.0 (June 2026)"

QUESTION = {
 1:  "Why has the SBTi strengthened the rules for scope 2 (electricity) emissions in Version 2.0?",
 2:  "What are the two options for setting scope 2 targets under Version 2.0?",
 3:  "How are scope 2 emissions reduction targets set under Version 2.0?",
 4:  "What does anchoring targets in the physical inventory mean for low-carbon electricity procurement?",
 5:  "What direct actions does the Standard prioritize for reducing electricity emissions?",
 6:  "How does Version 2.0 treat market instruments for low-carbon electricity?",
 7:  "What are the new scope 2 integrity criteria in Version 2.0?",
 8:  "What is the deliverability requirement for scope 2 market instruments (the 'near' principle)?",
 9:  "What is the 15-year age limit for scope 2 market instruments (the 'new' principle)?",
 10: "Is hourly matching of scope 2 emissions mandatory under Version 2.0 (the 'now' principle)?",
 11: "What is the SBTi's outlook for scope 2 and energy sector decarbonization?",
}

ALT = {
 1:  ["What are scope 2 emissions?", "What does Version 2.0 change about electricity emissions?",
      "Why does the Standard focus on decarbonizing electricity?"],
 2:  ["What types of scope 2 targets can companies set?", "What is a low-carbon electricity alignment target?",
      "Which companies are required to set scope 2 emissions reduction targets?"],
 3:  ["What is the new approach to scope 2 target setting?",
      "Are scope 2 targets based on location-based or market-based emissions?",
      "What are regionalized power pathways?"],
 4:  ["Is low-carbon electricity procurement still important under Version 2.0?",
      "How does Version 2.0 separate target ambition from target implementation?",
      "How do market-based actions count toward scope 2 target progress?"],
 5:  ["What sits at the top of the implementation hierarchy for electricity?",
      "How should companies prioritize scope 2 actions?",
      "What counts as direct action for electricity emissions?"],
 6:  ["Can companies still use market instruments for scope 2?",
      "What role do market instruments play in the Standard?",
      "Why does the Standard recognize market instruments for low-carbon electricity?"],
 7:  ["What are the near, new and now principles for scope 2?",
      "How does Version 2.0 strengthen scope 2 integrity?",
      "What integrity requirements apply to market-based electricity procurement?"],
 8:  ["What does 'near' mean in the scope 2 integrity criteria?",
      "What is deliverability for low-carbon electricity?",
      "Which market instruments are exempt from the deliverability requirement?"],
 9:  ["What does 'new' mean in the scope 2 integrity criteria?",
      "How old can a low-carbon project be for its market instruments to qualify?",
      "What are the exceptions to the 15-year age limit?"],
 10: ["What does 'now' mean in the scope 2 integrity criteria?", "What is hourly matching?",
      "Which companies must report hourly matching performance?",
      "What is the annual matching requirement for scope 2?"],
 11: ["What is next for scope 2 in the Standard?",
      "How will the SBTi work with the GHG Protocol on scope 2?"],
}

TAGS = {
 1:  ["scope 2", "electricity", "overview"],
 2:  ["scope 2", "target setting", "low-carbon electricity"],
 3:  ["scope 2", "location-based", "target setting"],
 4:  ["scope 2", "procurement", "claims"],
 5:  ["scope 2", "implementation hierarchy", "direct action"],
 6:  ["scope 2", "market instruments", "low-carbon electricity"],
 7:  ["scope 2", "integrity", "market instruments"],
 8:  ["scope 2", "deliverability", "market instruments"],
 9:  ["scope 2", "market instruments", "project age limit"],
 10: ["scope 2", "hourly matching", "time-matching"],
 11: ["scope 2", "outlook", "GHG Protocol"],
}

BASE = ("AI-extracted from the SBTi 'Understanding Scope 2' explainer PDF (text layer); "
        "answer verbatim (paragraph and bullet structure preserved); question, alternates, "
        "and tags authored; pending SME review.")
NOTE = {
 1:  BASE + " Source has no heading here; this is the document's opening (introduction).",
 7:  BASE + " The 'Raising the bar for scope 2 integrity' section is split into this overview plus its near / new / now sub-principles (s2-008..s2-010).",
 8:  BASE + " Sub-principle of 'Raising the bar for scope 2 integrity' (near).",
 9:  BASE + " Sub-principle of 'Raising the bar for scope 2 integrity' (new).",
 10: BASE + " Sub-principle of 'Raising the bar for scope 2 integrity' (now). Overlaps with faq-010 (scope 2 time-matching); SME to pick one canonical answer.",
}


def main():
    units = [json.loads(l) for l in open(IN, encoding="utf-8")]
    rows = []
    for u in units:
        n = u["num"]
        rows.append({
            "id": f"s2-{n:03d}",
            "question": QUESTION[n],
            "answer": u["answer"],
            "alternate_questions": ";".join(ALT.get(n, [])),
            "tags": ";".join(TAGS.get(n, ["scope 2"])),
            "source": SRC,
            "source_section": u["section"],
            "status": "draft", "owner": "", "reviewer": "", "last_reviewed": "",
            "version": "0.1",
            "notes": NOTE.get(n, BASE),
        })
    with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HEADER, quoting=csv.QUOTE_MINIMAL)
        w.writeheader(); w.writerows(rows)

    # integrity checks
    ids = [r["id"] for r in rows]
    assert len(ids) == len(set(ids)), "duplicate ids"
    assert all(r["id"] and r["question"] and r["answer"] for r in rows), "missing required field"
    banned = ("—", "–", "--")
    for r in rows:
        for fld in ("question", "alternate_questions", "tags", "source", "source_section", "notes"):
            for b in banned:
                assert b not in r[fld], f"banned char {b!r} in {r['id']}.{fld}"
    print(f"rows: {len(rows)} | unique ids ok | required fields ok | no em/en/double dash in authored fields")

    # round-trip: re-read, confirm 13 cols and multiline preservation
    back = list(csv.DictReader(open(OUT, encoding="utf-8-sig")))
    assert all(len(r) == 13 for r in back), "column count drift"
    ml = sum(1 for r in back if "\n" in r["answer"])
    assert all(b["answer"] == r["answer"] for b, r in zip(back, rows)), "answer round-trip mismatch"
    print(f"round-trip ok | rows with multiline answers: {ml}/{len(back)} | -> {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
