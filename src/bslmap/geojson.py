import csv
import json
from pathlib import Path
from typing import Dict, List, Any
from tqdm import tqdm

def build_geojson(labs_csv: Path, evidence_csv: Path, out_geojson: Path) -> None:
    print("Building GeoJSON from labs and evidence data...")
    
    # naive join by institution (improve later with alias table)
    ev_by_inst: Dict[str, List[Dict[str, Any]]] = {}
    
    print("Loading evidence data...")
    with evidence_csv.open() as f:
        r = csv.DictReader(f)
        evidence_rows = list(r)
        
    with tqdm(total=len(evidence_rows), desc="Indexing evidence", unit="row") as pbar:
        for row in evidence_rows:
            ev_by_inst.setdefault(row["institution"], []).append(row)
            pbar.update(1)

    print(f"\nProcessing labs data...")
    features = []
    with labs_csv.open() as f:
        r = csv.DictReader(f)
        labs_rows = list(r)
        
    with tqdm(total=len(labs_rows), desc="Building GeoJSON features", unit="lab") as pbar:
        for lab in labs_rows:
            ev = ev_by_inst.get(lab["institution"], [])
            features.append({
                "type": "Feature",
                "properties": {
                    **lab,
                    "evidence_count": len(ev),
                    "evidence_pmids": [e["pmid"] for e in ev][:50],
                },
                "geometry": {
                    "type":"Point",
                    "coordinates":[float(lab["longitude"]), float(lab["latitude"])]
                }
            })
            if ev:
                pbar.set_postfix_str(f"Evidence: {len(ev)} records")
            pbar.update(1)
    
    print(f"\nWriting GeoJSON with {len(features)} features...")
    geojson_data = {"type":"FeatureCollection","features":features}
    out_geojson.write_text(json.dumps(geojson_data, indent=2), encoding="utf-8")
    print(f"GeoJSON building completed. Output: {out_geojson}")