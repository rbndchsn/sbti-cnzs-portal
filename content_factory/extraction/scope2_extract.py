#!/usr/bin/env python3
"""
Extract verbatim source units from the SBTi 'Understanding Scope 2 in the Updated
Corporate Net-Zero Standard V2.0' explainer (6 pp., Google Docs export).

Fidelity method (matches content_factory rules):
- Words come from the embedded PDF text layer only (character-exact), never OCR.
- Section headings are Arial-Bold 11.5. Front matter (18pt title + 'Disclaimer' block) is
  dropped at the '(c) SBTi 2026' line. Bold 11.0 runs are inline emphasis, treated as body.
- Blocks (paragraphs / bullets) are reconstructed by geometry: a vertical gap > 22 pt or a
  page change starts a new block; a bullet glyph starts a new bullet; indented wrapped lines
  (x0 ~ 92.9) rejoin the current bullet. Line-end hyphens are preserved so compounds
  ('low-carbon', 'round-the-clock') stay intact. Only whitespace is normalized.
- The long 'Raising the bar for scope 2 integrity' section is split into an overview unit
  plus its Near / New / Now sub-principles, each a distinct askable topic.

Output: staging/scope2_units.jsonl  (verbatim answers + source_section; questions authored
later in build_scope2_csv.py).
"""
import fitz, re, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # content_factory/
PDF  = os.path.join(ROOT, "sources",
       "Understanding-Scope-2-in-the-Updated-Corporate-Net-Zero-Standard-V2.0.pdf")
OUT  = os.path.join(ROOT, "staging", "scope2_units.jsonl")

BULLET = "●"   # the source bullet glyph
DOT    = "•"   # rendered bullet glyph in answers (matches FAQ output)
GAP    = 22.0       # > GAP pt vertical gap => new block (wrap is ~14.6, break is ~29)
INDENT = 85.0       # x0 above this => wrapped bullet-continuation line


def get_lines():
    doc = fitz.open(PDF); rows = []
    for pno in range(len(doc)):
        for b in doc[pno].get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                spans = [s for s in l["spans"] if s["text"].strip()]
                if not spans:
                    continue
                txt = "".join(s["text"] for s in l["spans"]).replace("​", "").replace("\f", "").rstrip()
                if not txt.strip():
                    continue
                rows.append({
                    "p": pno + 1, "x0": l["bbox"][0], "y0": l["bbox"][1],
                    "size": max(s["size"] for s in spans),
                    "bold": all("Bold" in s["font"] for s in spans),
                    "t": txt,
                })
    return rows


def join_wrap(acc, t):
    """Rejoin a wrapped line. Keep a line-end hyphen (real compound), else single space."""
    if not acc:
        return t
    return acc + t if acc.endswith("-") else acc + " " + t


def build_blocks(rows):
    """Reconstruct ordered blocks: {'kind': 'H'|'P'|'B', 'text': str, 'p': int}."""
    blocks = []; cur = None; prev = None
    for r in rows:
        t = r["t"]
        if re.fullmatch(r"\d{1,2}", t.strip()):   # standalone page number
            continue
        if r["size"] < 9:                          # 8pt footer page number
            continue
        if r["size"] >= 14:                        # 18pt title (front matter)
            continue

        is_bullet = t.lstrip().startswith(BULLET)
        indent    = r["x0"] > INDENT
        is_head   = r["bold"] and r["size"] >= 11.4

        if is_bullet:
            kind = "B"; txt = t.lstrip().lstrip(BULLET).strip()
        elif indent:
            kind = "CONT"; txt = t.strip()
        elif is_head:
            kind = "H"; txt = t.strip()
        else:
            kind = "P"; txt = t.strip()

        # a continuation line always merges into the current block (the open bullet/paragraph)
        if kind == "CONT":
            if cur is None:
                cur = {"kind": "P", "text": txt, "p": r["p"]}
            else:
                cur["text"] = join_wrap(cur["text"], txt)
            prev = r
            continue

        samepage = prev is not None and r["p"] == prev["p"]
        gap = (r["y0"] - prev["y0"]) if samepage else 999.0
        boundary = (cur is None or is_bullet or not samepage or gap > GAP
                    or cur["kind"] != kind)

        if boundary:
            if cur:
                blocks.append(cur)
            cur = {"kind": kind, "text": txt, "p": r["p"]}
        else:
            cur["text"] = join_wrap(cur["text"], txt)
        prev = r

    if cur:
        blocks.append(cur)
    return blocks


def render(blocks):
    """Paragraphs and bullet-lists joined by blank line; bullets within a list by newline."""
    parts = []; i = 0
    while i < len(blocks):
        if blocks[i]["kind"] == "B":
            lst = []
            while i < len(blocks) and blocks[i]["kind"] == "B":
                lst.append(DOT + " " + re.sub(r"\s+", " ", blocks[i]["text"]).strip())
                i += 1
            parts.append("\n".join(lst))
        else:
            parts.append(re.sub(r"\s+", " ", blocks[i]["text"]).strip())
            i += 1
    return "\n\n".join(parts).strip()


def main():
    blocks = build_blocks(get_lines())

    # drop front matter: everything up to and including the copyright line
    start = 0
    for i, b in enumerate(blocks):
        if b["text"].strip().startswith("© SBTi") or b["text"].strip().startswith("(c) SBTi"):
            start = i + 1
            break
    blocks = blocks[start:]

    # group blocks into sections by heading; text before the first heading is the Introduction
    sections = []; head = "Introduction"; buf = []
    for b in blocks:
        if b["kind"] == "H":
            sections.append((head, buf)); head = b["text"]; buf = []
        else:
            buf.append(b)
    sections.append((head, buf))

    units = []
    n = 0
    for head, blks in sections:
        if not blks:
            continue
        if head.lower().startswith("raising the bar"):
            # split into overview + Near / New / Now sub-principles
            overview = []; subs = []; cur_name = None; cur_blocks = None
            label = {"Near": "Near (deliverability)",
                     "New":  "New (project age limit)",
                     "Now":  "Now (hourly matching)"}
            for b in blks:
                m = re.match(r"^(Near|New|Now):", b["text"])
                if m:
                    if cur_name:
                        subs.append((cur_name, cur_blocks))
                    cur_name = m.group(1); cur_blocks = [b]
                elif cur_name:
                    cur_blocks.append(b)
                else:
                    overview.append(b)
            if cur_name:
                subs.append((cur_name, cur_blocks))
            n += 1
            units.append({"num": n, "section": head, "answer": render(overview)})
            for name, cb in subs:
                n += 1
                units.append({"num": n, "section": f"{head}: {label[name]}", "answer": render(cb)})
        else:
            n += 1
            units.append({"num": n, "section": head, "answer": render(blks)})

    with open(OUT, "w", encoding="utf-8") as f:
        for u in units:
            f.write(json.dumps(u, ensure_ascii=False) + "\n")

    print(f"units: {len(units)} -> {os.path.relpath(OUT, ROOT)}\n")
    for u in units:
        wc = len(u["answer"].split())
        print(f"[{u['num']:>2}] {u['section']}  ({wc} words)")
    print("\n===== FULL DUMP =====")
    for u in units:
        print(f"\n--- s2-{u['num']:03d} | {u['section']} ---\n{u['answer']}")


if __name__ == "__main__":
    main()
