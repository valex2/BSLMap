import re
from pathlib import Path
from collections import defaultdict
from tqdm import tqdm
from bslmap.io_utils import read_jsonl
import csv

def merge_extractions(in_jsonl: Path, out_csv: Path) -> None:
    print("Consolidating extractions...")
    
    by_pmid = defaultdict(list)
    records = list(read_jsonl(in_jsonl))
    
    print(f"Processing {len(records)} extraction records...")
    with tqdm(total=len(records), desc="Grouping by PMID", unit="record") as pbar:
        for r in records:
            m = re.match(r"pmid:(\d+)", r.get("doc_id",""))
            if not m:
                pbar.update(1)
                continue
            by_pmid[m.group(1)].append(r)
            pbar.update(1)

    print(f"\nMerging {len(by_pmid)} unique PMIDs...")
    rows = []
    with tqdm(total=len(by_pmid), desc="Selecting best extractions", unit="pmid") as pbar:
        for pmid, recs in by_pmid.items():
            best = sorted(recs, key=lambda x: x.get("confidence", 0), reverse=True)[0]
            rows.append({
                "pmid": pmid,
                "lab_name": best.get("lab_name",""),
                "institution": best.get("institution",""),
                "country": best.get("country",""),
                "city": best.get("city",""),
                "bsl_level_inferred": best.get("bsl_level_inferred",""),
                "pathogens": "; ".join(best.get("pathogens", []) or []),
                "research_types": "; ".join(best.get("research_types", []) or []),
                "ppp_or_gof": best.get("ppp_or_gof", False),
                "confidence": best.get("confidence", 0.0),
                "source_pmid": pmid
            })
            pbar.update(1)

    print(f"\nWriting {len(rows)} consolidated records to CSV...")
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [
            "pmid","lab_name","institution","country","city","bsl_level_inferred",
            "pathogens","research_types","ppp_or_gof","confidence","source_pmid"
        ])
        w.writeheader()
        with tqdm(total=len(rows), desc="Writing CSV rows", unit="row") as pbar:
            for r in rows:
                w.writerow(r)
                pbar.update(1)
    
    print(f"Consolidation completed. Output: {out_csv}")