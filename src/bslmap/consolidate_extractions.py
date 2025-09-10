import re
from pathlib import Path
from collections import defaultdict
from tqdm import tqdm
from bslmap.io_utils import read_jsonl
import csv
from typing import Dict, List, Optional

def load_labs_data(project_root: Path) -> Dict[str, Dict]:
    """Load institution data from labs.csv."""
    labs_path = project_root / "data" / "labs.csv"
    if not labs_path.exists():
        print(f"Warning: {labs_path} not found. No institution data will be included.")
        return {}
    
    labs = {}
    with open(labs_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Use institution name as key for lookup
            labs[row['institution'].lower()] = {
                'institution': row['institution'],
                'country': row.get('country', ''),
                'city': row.get('city', ''),
                'latitude': row.get('latitude', ''),
                'longitude': row.get('longitude', '')
            }
    return labs

def merge_extractions(in_jsonl: Path, out_csv: Path, corpus_jsonl: Optional[Path] = None) -> None:
    print("Consolidating extractions...")
    
    # Load institution data
    project_root = Path(__file__).parent.parent.parent
    labs_data = load_labs_data(project_root)
    
    # Load corpus data if provided
    corpus = []
    if corpus_jsonl and corpus_jsonl.exists():
        corpus = list(read_jsonl(corpus_jsonl))
    
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
            
            # Get the original corpus record to extract institution information
            corpus_rec = {}
            if corpus:
                corpus_rec = next((r for r in corpus if r.get("doc_id", "").startswith(f"pmid:{pmid}")), {})
            
            # Try to find matching institution data
            institution_match = None
            
            # First, check if we have direct institution info in the extraction
            if "institution" in best and best["institution"]:
                inst_name = best["institution"].lower()
                if inst_name in labs_data:
                    institution_match = labs_data[inst_name]
            
            # If no direct match, try to find in evidence spans
            if not institution_match:
                evidence = ". ".join(best.get("evidence_spans", [""])).lower()
                if evidence and labs_data:
                    if DEBUG := False:  # Set to True for debugging
                        print(f"\nProcessing PMID: {pmid}")
                        print(f"Evidence: {evidence[:200]}...")
                    
                    # Try different matching strategies
                    for inst_name, inst_data in labs_data.items():
                        # 1. Check for exact match
                        if inst_name.lower() in evidence:
                            if DEBUG:
                                print(f"Found exact match for: {inst_name}")
                            institution_match = inst_data
                            break
                            
                        # 2. Check for partial match using common abbreviations
                        inst_lower = inst_name.lower()
                        if "national institute of allergy and infectious diseases" in inst_lower:
                            # Check for common abbreviations and partial matches
                            if any(term in evidence for term in ["niaid", "national institute of allergy", "nih"]):
                                if DEBUG:
                                    print(f"Found partial/abbreviation match for: {inst_name}")
                                institution_match = inst_data
                                break
            
            # Get institution from corpus record if available, otherwise from extraction or labs_data
            institution = (
                corpus_rec.get("aff_hint", "") or 
                best.get("institution", "") or 
                (institution_match["institution"] if institution_match else "")
            )
            
            # Prepare the row with or without institution data
            row = {
                "pmid": pmid,
                "lab_name": best.get("lab_name", ""),
                "institution": institution,
                "country": institution_match.get("country", "") if institution_match else "",
                "city": institution_match.get("city", "") if institution_match else "",
                "latitude": institution_match.get("latitude", "") if institution_match else "",
                "longitude": institution_match.get("longitude", "") if institution_match else "",
                "bsl_level_inferred": best.get("bsl_level_inferred", ""),
                "pathogens": "; ".join(best.get("pathogens", []) or []),
                "research_types": "; ".join(best.get("research_types", []) or []),
                "ppp_or_gof": best.get("ppp_or_gof", False),
                "confidence": best.get("confidence", 0.0),
                "source_pmid": pmid
            }
            rows.append(row)
            pbar.update(1)

    print(f"\nWriting {len(rows)} consolidated records to CSV...")
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "pmid", "lab_name", "institution", "country", "city", 
            "latitude", "longitude", "bsl_level_inferred",
            "pathogens", "research_types", "ppp_or_gof", "confidence", "source_pmid"
        ]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        with tqdm(total=len(rows), desc="Writing CSV rows", unit="row") as pbar:
            for r in rows:
                w.writerow(r)
                pbar.update(1)
    
    print(f"Consolidation completed. Output: {out_csv}")