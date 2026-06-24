#!/usr/bin/env python3
"""Build the draft qa CSV (exact portal schema) from glossary_units.jsonl.
Answers are verbatim (untouched). Questions/alternates/tags are the AUTHORED layer
and ship as status=draft for SME review. ID namespace: kt-### (Key Terms)."""
import json, csv, re

HEADER=["id","question","answer","alternate_questions","tags","source",
        "source_section","status","owner","reviewer","last_reviewed","version","notes"]

PLURAL_HEADS={"arrangements","targets","outcomes","emissions","goods","contributions",
              "constraints","activities","pools","options","funding"}

TAG_RULES=[
 (r"scope 1","scope 1"),(r"scope 2","scope 2"),(r"scope 3","scope 3"),
 (r"near-term","near-term targets"),(r"long-term|long-lived","long-term"),
 (r"net-zero","net-zero"),(r"target","targets"),(r"assur","assurance"),
 (r"verif|valid","verification"),(r"account","accounting"),(r"invent","inventory"),
 (r"removal|neutrali|sequest","removals"),(r"electricit|LCE|energy attribute|grid","electricity"),
 (r"market instrument|certificate|chain-of-custody|book-and-claim","market instruments"),
 (r"residual","residual emissions"),(r"base year","base year"),
 (r"value chain|supplier|category","value chain"),(r"fossil","fossil fuels"),
 (r"carbon credit|GHG credit|mitigation outcome","carbon credits"),
 (r"governance|transition plan|disclos","governance"),
]

def is_plural(term):
    last=re.sub(r"[^a-z]","",term.lower().split()[-1])
    return last in PLURAL_HEADS or (last.endswith("s") and last not in
        {"analysis","basis","emissions","status","process","bias","ibid"})

def canonical(term):
    return f"What are {term}?" if is_plural(term) else f"What is {term}?"

def acronyms(term,ans):
    found=[]
    for m in re.findall(r"\(([A-Z][A-Za-z]*[A-Z][A-Za-z]*s?)\)",ans):
        if 2<=len(m)<=6 and m.lower()!=term.lower(): found.append(m)
    return list(dict.fromkeys(found))[:2]

def alternates(term,ans):
    alts=[f"What does {term} mean?",
          f"Define {term}",
          f"{term} definition",
          f"How does the SBTi Corporate Net-Zero Standard define {term}?",
          term]
    for a in acronyms(term,ans):
        alts.append(f"What is {a}?"); alts.append(a)
    # dedupe preserving order, drop empties/dups vs canonical
    seen=set(); out=[]
    for a in alts:
        k=a.lower()
        if a and k not in seen: seen.add(k); out.append(a)
    return out

def tags(term,ans):
    blob=(term+" "+ans).lower(); t=[]
    for pat,tag in TAG_RULES:
        if re.search(pat,blob,re.I) and tag not in t: t.append(tag)
    if not t: t=["definitions"]
    return (["definitions"]+t)[:4]

def main():
    units=[json.loads(l) for l in open("glossary_units.jsonl",encoding="utf-8")]
    def junk(u):
        t=u["term"].strip(); a=u["answer"].strip()
        return (a=="Definition" or "table lists" in t.lower()
                or "Corporate Net-Zero Standard" in t or t.endswith(". Term") or len(t)<2)
    units=[u for u in units if not junk(u)]
    rows=[]
    for i,u in enumerate(units,1):
        term=u["term"]; ans=u["answer"]
        rows.append({
            "id":f"kt-{i:03d}",
            "question":canonical(term),
            "answer":ans,
            "alternate_questions":";".join(alternates(term,ans)),
            "tags":";".join(tags(term,ans)),
            "source":u["source"],
            "source_section":u["source_section"],
            "status":"draft",
            "owner":"",
            "reviewer":"",
            "last_reviewed":"",
            "version":"0.1",
            "notes":"AI-drafted from SBTi CNZS v2.0 PDF text layer (Key Terms table, pp.85-101); answer verbatim; pending SME review.",
        })
    with open("sbti_cnzs_v2_qa.csv","w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=HEADER,quoting=csv.QUOTE_MINIMAL)
        w.writeheader(); w.writerows(rows)
    # validation mirror of validate_qa.py
    ids=[r["id"] for r in rows]
    assert len(ids)==len(set(ids)),"duplicate ids"
    assert all(r["id"] and r["question"] and r["answer"] for r in rows),"missing required"
    print(f"rows: {len(rows)}  | unique ids ok | required fields ok")
    print("\n=== sample rows ===")
    for r in rows[:2]+rows[40:41]:
        print(f"\n{r['id']} | {r['question']}")
        print(f"  alt: {r['alternate_questions']}")
        print(f"  tags: {r['tags']}")
        print(f"  ans: {r['answer'][:110]}...")

if __name__=="__main__": main()
