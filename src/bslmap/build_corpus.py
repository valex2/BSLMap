from pathlib import Path
from typing import List, Dict
from tqdm import tqdm
from bslmap.io_utils import read_jsonl, write_jsonl
from bslmap.cfg import Settings

def _chunk(text: str, target: int, overlap: int) -> List[str]:
    if not text:
        return []
    words = text.split()
    step = max(1, target - overlap)
    chunks = []
    for i in range(0, len(words), step):
        chunk = " ".join(words[i:i+target])
        if chunk:
            chunks.append(chunk)
    return chunks

def _links_index(eupmc_jsonl: Path) -> Dict[str, list]:
    idx: Dict[str, list] = {}
    records = list(read_jsonl(eupmc_jsonl))
    
    with tqdm(total=len(records), desc="Indexing EUPMC links", unit="record") as pbar:
        for r in records:
            pmid = r.get("pmid")
            if not pmid:
                pbar.update(1)
                continue
            idx.setdefault(pmid, []).append(r)
            pbar.update(1)
    
    return idx

def build_corpus(pubmed_jsonl: Path, eupmc_jsonl: Path, out_jsonl: Path) -> None:
    cfg = Settings()
    print("Building corpus from PubMed and EUPMC data...")
    
    _links_index(eupmc_jsonl)  # Index available for future use
    rows = []
    
    # Read all records first to get total count for progress bar
    pubmed_records = list(read_jsonl(pubmed_jsonl))
    print(f"Processing {len(pubmed_records)} PubMed records...")
    
    with tqdm(total=len(pubmed_records), desc="Building corpus", unit="record") as pbar:
        for rec in pubmed_records:
            pmid = rec.get("pmid")
            title = rec.get("title","")
            abstract = rec.get("abstract","")
            fulltext = ""  # (keep abstract MVP; add fetchers if you want)
            text = fulltext if fulltext else abstract
            
            if not text:
                pbar.update(1)
                continue
                
            chunks = _chunk(text, cfg.chunk_target_tokens, cfg.chunk_overlap_tokens)
            for i, ch in enumerate(chunks):
                rows.append({
                    "doc_id": f"pmid:{pmid}#chunk{i}",
                    "source": "pubmed",
                    "title": title,
                    "aff_hint": rec.get("institution_query",""),
                    "text": ch,
                    "metadata": {
                        "pmid": pmid,
                        "journal": rec.get("fulljournalname",""),
                        "mesh_terms": rec.get("mesh_heading_list", []),
                    }
                })
            
            if len(chunks) > 1:
                pbar.set_postfix_str(f"Generated {len(chunks)} chunks")
            pbar.update(1)
    
    print(f"\nWriting {len(rows)} corpus entries to {out_jsonl}...")
    write_jsonl(out_jsonl, rows)
    print(f"Corpus building completed. Total entries: {len(rows)}")