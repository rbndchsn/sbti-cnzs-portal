#!/usr/bin/env python3
"""Build draft qa CSV (portal schema) from faq_units.jsonl.
Canonical question = SBTi's verbatim wording. Answer = verbatim (bullets preserved).
Alternates hand-authored (n=12). status=draft. ID namespace: faq-###."""
import json, csv

HEADER=["id","question","answer","alternate_questions","tags","source",
        "source_section","status","owner","reviewer","last_reviewed","version","notes"]
SRC="SBTi Corporate Net-Zero Standard V2.0 — Frequently Asked Questions (June 2026)"

ALT={
 1:["What's new in V2.0?","What are the key innovations in the Corporate Net-Zero Standard V2.0?","What changed in the new SBTi standard?","Summary of changes in Version 2.0"],
 2:["What are the benefits of using the Standard?","Why adopt the Corporate Net-Zero Standard?","What's the business case for the SBTi standard?"],
 3:["How does the Standard apply to Global South companies?","What does V2.0 offer companies in developing economies?","Global South flexibilities in the Standard"],
 4:["Is V2.0 still science-based?","Is the new standard aligned with 1.5°C?","Has the Standard kept its scientific integrity?"],
 5:["Which version should I use to set targets?","V1.3.1 vs V2.0 — which applies to my company?","When should companies switch to Version 2.0?","Is Version 1 still open for target submission?"],
 6:["What if a company is off-track on its 2030 targets?","What happens if we miss our 2030 target?","How does the Standard treat companies behind on their targets?"],
 7:["How does V2.0 relate to the ISO net-zero standard?","Does the SBTi standard conflict with ISO?","SBTi versus ISO net-zero standard"],
 8:["How does V2.0 align with the GHG Protocol revision?","What is the relationship between the Standard and the GHG Protocol?","Does the Standard reflect upcoming GHGP changes?"],
 9:["How do project-based interventions count toward targets?","What role do projects play in target implementation?","How are interventions treated in the Standard?"],
 10:["Why is hourly matching for scope 2 optional?","Why isn't scope 2 time-matching mandatory?","Is scope 2 time-matching required?"],
 11:["Will the SBTi accredit carbon credit programmes?","Does the SBTi approve certificate or credit issuers?","How will the SBTi handle market instrument programmes?"],
 12:["When can companies start using V2.0?","Is Version 2.0 available now?","When are the V2.0 innovations available to Version 1 users?"],
}
TAGS={
 1:["overview","what's new","target setting"],
 2:["overview","business case","transition risk"],
 3:["global south","flexibilities","scope 3"],
 4:["science-based","1.5C","integrity"],
 5:["versions","transition","target setting"],
 6:["targets","progress","best-efforts"],
 7:["interoperability","ISO","net-zero standard"],
 8:["interoperability","GHG Protocol","scope accounting"],
 9:["implementation","projects","inventory"],
 10:["scope 2","time-matching","electricity"],
 11:["market instruments","carbon credits","accreditation"],
 12:["timeline","availability","versions"],
}

def main():
    units=[json.loads(l) for l in open("faq_units.jsonl",encoding="utf-8")]
    rows=[]
    for u in units:
        n=u["num"]
        rows.append({
            "id":f"faq-{n:03d}",
            "question":u["question"],
            "answer":u["answer"],
            "alternate_questions":";".join(ALT.get(n,[])),
            "tags":";".join(TAGS.get(n,["overview"])),
            "source":SRC,
            "source_section":f"{u['section']} — Q{n}",
            "status":"draft","owner":"","reviewer":"","last_reviewed":"",
            "version":"0.1",
            "notes":"AI-extracted from SBTi CNZS V2.0 official FAQ PDF; question and answer verbatim (bullet structure preserved); alternates authored; pending SME review.",
        })
    with open("sbti_cnzs_v2_faq_qa.csv","w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=HEADER,quoting=csv.QUOTE_MINIMAL)
        w.writeheader(); w.writerows(rows)
    ids=[r["id"] for r in rows]
    assert len(ids)==len(set(ids)) and all(r["id"] and r["question"] and r["answer"] for r in rows)
    print(f"rows: {len(rows)} | unique ids ok | required fields ok")
    # round-trip check: read back, confirm 13 cols & multiline answers intact
    back=list(csv.DictReader(open("sbti_cnzs_v2_faq_qa.csv",encoding="utf-8-sig")))
    assert all(len(r)==13 for r in back)
    ml=sum(1 for r in back if "\n" in r["answer"])
    print(f"round-trip ok | rows with multiline answers: {ml}/{len(back)}")
if __name__=="__main__": main()
