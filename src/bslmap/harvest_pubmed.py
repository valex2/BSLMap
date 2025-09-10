import re
import time

import httpx
from typing import List, Dict, Any
from tqdm import tqdm
from bslmap.cfg import Settings

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def _esearch(q: str, email: str, retmax: int) -> List[str]:
    params = {"db":"pubmed","term": q,"retmode":"json","retmax": retmax,"email": email}
    r = httpx.get(f"{BASE}/esearch.fcgi", params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("esearchresult", {}).get("idlist", [])

def _esummary(ids: List[str], email: str) -> Dict[str, Any]:
    if not ids:
        return {}
    
    # Batch requests to avoid URI too long errors
    batch_size = 200  # Conservative batch size
    all_results = {"result": {"uids": []}}
    
    num_batches = (len(ids) + batch_size - 1) // batch_size
    with tqdm(total=num_batches, desc="Fetching summaries", unit="batch") as pbar:
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i + batch_size]
            params = {"db":"pubmed","id":",".join(batch_ids),"retmode":"json","email": email}
            r = httpx.get(f"{BASE}/esummary.fcgi", params=params, timeout=30)
            r.raise_for_status()
            batch_result = r.json()
            
            # Merge results
            if "result" in batch_result:
                all_results["result"]["uids"].extend(batch_result["result"].get("uids", []))
                for uid in batch_result["result"].get("uids", []):
                    if uid in batch_result["result"]:
                        all_results["result"][uid] = batch_result["result"][uid]
            
            pbar.update(1)
            
            # Rate limiting between batches
            if i + batch_size < len(ids):
                time.sleep(0.34)
    
    return all_results

def _efetch_abs(ids: List[str], email: str) -> str:
    if not ids:
        return ""
    
    # Batch requests to avoid URI too long errors
    batch_size = 200  # Conservative batch size
    all_xml = []
    
    num_batches = (len(ids) + batch_size - 1) // batch_size
    with tqdm(total=num_batches, desc="Fetching abstracts", unit="batch") as pbar:
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i + batch_size]
            params = {"db":"pubmed","id":",".join(batch_ids),"retmode":"xml","email": email}
            r = httpx.get(f"{BASE}/efetch.fcgi", params=params, timeout=60)
            r.raise_for_status()
            all_xml.append(r.text)
            
            pbar.update(1)
            
            # Rate limiting between batches
            if i + batch_size < len(ids):
                time.sleep(0.34)
    
    return "\n".join(all_xml)

def _parse_abs(xml_text: str) -> Dict[str,str]:
    blocks = re.split(r"</PubmedArticle>", xml_text)
    out = {}
    for b in blocks:
        m_id = re.search(r"<PMID[^>]*>(\d+)</PMID>", b)
        if not m_id:
            continue
        pmid = m_id.group(1)
        texts = re.findall(r"<AbstractText[^>]*>(.*?)</AbstractText>", b, flags=re.S|re.M)
        txt = re.sub(r"<[^>]+>", " ", " ".join(texts))
        out[pmid] = re.sub(r"\s+"," ",txt).strip()
    return out

def _build_query(inst: str, kws: List[str], since: int) -> str:
    aff = f'("{inst}"[AD])'
    kw = " OR ".join([f'"{k}"[TIAB]' for k in kws])
    date = f'("{since}"[PDAT] : "3000"[PDAT])'
    return f'({aff}) AND ({kw}) AND {date}'

def search_pubmed(institutions: List[str], keywords: List[str], cfg: Settings) -> List[Dict[str, Any]]:
    out = []
    print(f"Searching PubMed for {len(institutions)} institutions...")
    
    with tqdm(total=len(institutions), desc="Processing institutions", unit="inst") as pbar:
        for inst in institutions:
            pbar.set_postfix_str(f"Current: {inst[:50]}..." if len(inst) > 50 else inst)
            
            q = _build_query(inst, keywords, cfg.since_year)
            pmids = _esearch(q, cfg.email_for_ncbi, cfg.max_per_institution)
            pbar.write(f"Found {len(pmids)} PMIDs for {inst}")
            
            time.sleep(0.34)
            meta = _esummary(pmids, cfg.email_for_ncbi)
            time.sleep(0.34)
            xml = _efetch_abs(pmids, cfg.email_for_ncbi)
            abs_map = _parse_abs(xml)

            uids = meta.get("result", {}).get("uids", [])
            for uid in uids:
                rec = meta["result"].get(uid, {})
                rec["pmid"] = uid
                rec["abstract"] = abs_map.get(uid, "")
                rec["institution_query"] = inst
                out.append(rec)
            
            pbar.update(1)
    
    print(f"\nCompleted PubMed search. Total records: {len(out)}")
    return out