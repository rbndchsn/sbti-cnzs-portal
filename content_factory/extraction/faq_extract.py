#!/usr/bin/env python3
"""Extract verbatim Q&A from the SBTi CNZS v2.0 official FAQ PDF (6 pp.).
Questions = SBTi's own wording; answers verbatim with bullet hierarchy.
Section headings detected by font (Arial-Bold 12), merging multi-line titles."""
import fitz, re, json

PDF="faq.pdf"; BULLET1="\u25cf"; BULLET2="\u25cb"
def get_lines():
    doc=fitz.open(PDF); out=[]
    for pno in range(len(doc)):
        for b in doc[pno].get_text("dict")["blocks"]:
            for l in b.get("lines",[]):
                txt="".join(s["text"] for s in l["spans"]).replace("\u200b","").replace("\f","").rstrip()
                if not txt.strip(): continue
                fonts=[s["font"] for s in l["spans"]]; sizes=[s["size"] for s in l["spans"]]
                is_head=all("Bold" in f for f in fonts) and max(sizes)>=11.5
                out.append({"p":pno,"t":txt,"head":is_head})
    return out

def main():
    L=[x for x in get_lines() if not re.fullmatch(r"\d{1,2}",x["t"].strip())]
    while L and ("FREQUENTLY ASKED QUESTIONS" in L[0]["t"] or "VERSION 2.0" in L[0]["t"] or L[0]["t"].strip()=="June 2026"):
        L.pop(0)
    # merge consecutive heading lines into section markers
    merged=[]; i=0
    while i<len(L):
        if L[i]["head"]:
            buf=[L[i]["t"]]; j=i+1
            while j<len(L) and L[j]["head"]: buf.append(L[j]["t"]); j+=1
            merged.append({"section":" ".join(buf).strip(),"q":None}); i=j
        else:
            merged.append({"line":L[i]["t"]}); i+=1
    # walk: track section + sequential questions
    entries=[]; section=None; expected=1
    cur=None
    def flush():
        nonlocal cur
        if cur is not None: entries.append(cur); cur=None
    for node in merged:
        if "section" in node:
            section=node["section"]; continue
        t=node["line"].strip()
        m=re.match(r"^(\d+)\.\s*(.*)$",t)
        if m and int(m.group(1))==expected:
            flush()
            cur={"num":expected,"section":section,"qparts":[m.group(2)],"abody":[]}
            expected+=1
        elif cur is not None:
            # still part of question if question not yet terminated and no bullet seen
            if not cur["abody"] and not t.startswith((BULLET1,BULLET2)) and not cur["qparts"][-1].rstrip().endswith(("?",":",".")):
                cur["qparts"].append(t)
            else:
                cur["abody"].append(t)
    flush()
    # render
    units=[]
    for e in entries:
        q=re.sub(r"\s+"," "," ".join(e["qparts"]).strip())
        items=[]; c=None
        for t in e["abody"]:
            if t.startswith(BULLET1):
                if c: items.append(c)
                c=("L1",t[1:].strip())
            elif t.startswith(BULLET2):
                if c: items.append(c)
                c=("L2",t[1:].strip())
            else:
                if c:
                    lvl,txt=c
                    txt=txt[:-1]+t if txt.endswith("-") else txt+" "+t
                    c=(lvl,txt)
                else: c=("P",t)
        if c: items.append(c)
        parts=[]
        for lvl,txt in items:
            txt=re.sub(r"\s+"," ",txt).strip()
            parts.append(txt if lvl=="P" else ("\u2022 "+txt if lvl=="L1" else "    \u25e6 "+txt))
        units.append({"num":e["num"],"question":q,"answer":"\n".join(parts).strip(),"section":e["section"]})
    with open("faq_units.jsonl","w",encoding="utf-8") as f:
        for u in units: f.write(json.dumps(u,ensure_ascii=False)+"\n")
    print(f"FAQ entries: {len(units)}\n")
    for u in units:
        print(f"Q{u['num']} | section: {u['section']}")
        print(f"   {u['question']}")
    print("\n=== full sample: Q1 and Q11 ===")
    for u in units:
        if u["num"] in (1,11):
            print(f"\n[Q{u['num']}] {u['question']}\n{u['answer']}")
if __name__=="__main__": main()
