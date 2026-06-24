#!/usr/bin/env python3
"""Reconstruct SBTi CNZS v2.0 glossary (Key Terms, pp.85-101) by geometry, line-aware.
Columns (same font): Term x<160 | Definition x>=160. Entry boundaries = vertical gaps
in the term column. Line-end hyphens are PRESERVED (join without space) so real
compounds like 'long-term', 'third-party' stay intact. Verbatim; nothing added/removed."""
import fitz, re, json

PDF="sources/Corporate-Net-Zero-Standard-version-2.pdf"; P_FIRST,P_LAST=85,101; COL_X=160
Y_TOP,Y_BOTTOM=58,772; GAP=18; YTOL=3
DROP_FONT=("Raleway",); INTRO=re.compile(r"(?i)complete list of SBTi|This table lists")

def page_lines(pno):
    raw=[]
    for b in fitz.open(PDF)[pno].get_text("dict")["blocks"]:
        for l in b.get("lines",[]):
            for s in l["spans"]:
                x0,y0=s["bbox"][0],s["bbox"][1]
                if not (Y_TOP<y0<Y_BOTTOM): continue
                if any(d in s["font"] for d in DROP_FONT): continue
                if s["size"]<9.5: continue
                if s["text"].strip(): raw.append((y0,x0,s["text"]))
    raw.sort(key=lambda r:(round(r[0],1),r[1]))
    lines=[]
    for y,x,t in raw:
        if lines and abs(lines[-1]["y"]-y)<=YTOL: lines[-1]["sp"].append((x,t))
        else: lines.append({"y":y,"sp":[(x,t)]})
    for ln in lines:
        ln["sp"].sort(key=lambda s:s[0])
        ln["term"]=" ".join(t for x,t in ln["sp"] if x<COL_X).strip()
        ln["def"] =" ".join(t for x,t in ln["sp"] if x>=COL_X).strip()
    return lines

def join_lines(parts):
    out=""
    for p in parts:
        p=p.strip()
        if not p: continue
        if not out: out=p
        elif out.endswith("-"): out=out+p          # keep hyphen, no space
        else: out=out+" "+p
    return re.sub(r"\s+"," ",out).strip()

def main():
    entries=[]
    for pno in range(P_FIRST-1,P_LAST):
        lines=page_lines(pno)
        # mark entry-start lines
        prev_term_y=None; starts=[]
        for i,ln in enumerate(lines):
            if ln["term"] and not INTRO.search(ln["term"]) and ln["term"]!="Term":
                if prev_term_y is None or (ln["y"]-prev_term_y)>GAP:
                    starts.append(i)
                prev_term_y=ln["y"]
        # content before first start -> continuation of previous entry's definition
        if starts:
            pre=[lines[j]["def"] for j in range(starts[0]) if lines[j]["def"] and not INTRO.search(lines[j]["def"])]
            if pre and entries: entries[-1][1].extend(pre)
        else:
            cont=[ln["def"] for ln in lines if ln["def"] and not INTRO.search(ln["def"])]
            if cont and entries: entries[-1][1].extend(cont)
            continue
        bounds=starts+[len(lines)]
        for k in range(len(starts)):
            seg=lines[bounds[k]:bounds[k+1]]
            term=join_lines([l["term"] for l in seg])
            dfn=[l["def"] for l in seg]
            if term in ("Term","Definition") or INTRO.search(term): continue
            entries.append([term,dfn])
    units=[]
    for term,defparts in entries:
        ans=join_lines(defparts)
        if not ans: continue
        units.append({"term":term,"answer":ans,
            "source":"SBTi Corporate Net-Zero Standard v2.0 (June 2026)",
            "source_section":f"Key Terms \u2014 {term}"})
    with open("glossary_units.jsonl","w",encoding="utf-8") as f:
        for u in units: f.write(json.dumps(u,ensure_ascii=False)+"\n")
    print(f"entries: {len(units)}")
    # audit hyphenated tokens for any suspicious mid-word splits
    hyph=set()
    for u in units:
        for tok in re.findall(r"\b\w+-\w+\b", u["answer"]):
            hyph.add(tok.lower())
    print("\nsample hyphenated compounds (should look like real words):")
    print(", ".join(sorted(h for h in hyph)[:40]))
    print("\n--- spot check entries ---")
    for name in ("Action","Long-lived removal","Net-zero target","Verified mitigation outcomes"):
        for u in units:
            if u["term"].lower()==name.lower():
                print(f"\n[{u['term']}] -> {u['source_section']}\n{u['answer']}")
                break

if __name__=="__main__": main()
