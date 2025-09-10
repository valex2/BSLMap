import os
import sys
import time
import json
import httpx
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from pathlib import Path

# Try to import tqdm, but don't fail if not available
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

# Import settings with fallback
class Settings:
    def __init__(self, **kwargs):
        self.europe_pmc_cc_by_only = kwargs.get('europe_pmc_cc_by_only', False)

# Try to import the real settings
try:
    from bslmap.cfg import Settings as RealSettings
    Settings = RealSettings
except ImportError:
    pass

def _links_for_pmid(pmid: str) -> List[Dict]:
    print(f"\n[DEBUG] _links_for_pmid called with PMID: {pmid}")
    try:
        url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
        query = f"EXT_ID:{pmid} AND SRC:MED"
        params = {"query": query, "resultType": "core", "format": "json"}
        
        # Print request details for debugging
        print(f"\n🔍 Querying Europe PMC for PMID: {pmid}")
        print(f"   URL: {url}")
        print(f"   Query: {query}")
        
        # Make the request with a timeout
        response = httpx.get(url, params=params, timeout=30.0)
        response.raise_for_status()
        
        data = response.json()
        hits = data.get("resultList", {}).get("result", [])
        print(f"   Found {len(hits)} hits")
        
        links = []
        for hit in hits:
            urls = hit.get("fullTextUrlList", {}).get("fullTextUrl", [])
            print(f"   Processing {len(urls)} URLs")
            
            for ll in urls:
                link_data = {
                    "pmid": pmid,
                    "url": ll.get("url"),
                    "type": ll.get("documentStyle"),
                    "site": ll.get("site"),
                    "license": hit.get("license", ""),
                    "hit_title": hit.get("title", "")[:50] + "..." if hit.get("title") else ""
                }
                links.append(link_data)
                print(f"   ✓ Found: {link_data['url']} ({link_data['type']})")
        
        return links
    except Exception as e:
        print(f"❌ Error processing PMID {pmid}: {str(e)}")
        if 'response' in locals():
            print(f"   Status code: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
        return []

def links_for_pmids(pmids: List[str], cfg: Settings):
    print("\n[DEBUG] links_for_pmids called")
    print(f"[DEBUG] Number of PMIDs: {len(pmids)}")
    print(f"[DEBUG] First 5 PMIDs: {pmids[:5]}")
    out = []
    total_pmids = len(pmids)
    print("[DEBUG] Starting processing...")
    
    # Print configuration
    print("\n" + "="*60)
    print("EUROPE PMC HARVESTER".center(60))
    print("="*60)
    print(f"Total PMIDs to process: {total_pmids:,}")
    print(f"CC-BY only: {getattr(cfg, 'europe_pmc_cc_by_only', False)}")
    print(f"Environment: Python {sys.version.split()[0]}")
    print(f"Working directory: {os.getcwd()}")
    print("="*60 + "\n")
    
    # Create a simple progress bar if tqdm is not working
    try:
        from tqdm import tqdm
        progress_bar = tqdm(
            total=total_pmids,
            desc="Processing",
            unit="pmid",
            bar_format='{l_bar}{bar:40}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]',
            file=sys.stdout
        )
        USE_TQDM = True
    except Exception as e:
        print(f"⚠️ tqdm not available, using simple progress: {e}")
        progress_bar = None
        USE_TQDM = False
    
    try:
        for i, pmid in enumerate(pmids, 1):
            try:
                if USE_TQDM:
                    progress_bar.set_postfix_str(f"PMID: {pmid}")
                else:
                    print(f"\n[{i}/{total_pmids}] Processing PMID: {pmid}")
                
                # Process the PMID
                links = _links_for_pmid(str(pmid).strip())
                
                # Filter for CC-BY if needed
                if getattr(cfg, 'europe_pmc_cc_by_only', False):
                    links = [x for x in links if x.get("license", "").upper().startswith("CC-BY")]
                
                # Add to results
                out.extend(links)
                
                # Log results
                if links:
                    msg = f"✅ Found {len(links)} links for PMID {pmid}"
                    if getattr(cfg, 'europe_pmc_cc_by_only', False):
                        msg += " (CC-BY only)"
                    print(msg)
                
                # Update progress
                if USE_TQDM:
                    progress_bar.update(1)
                
                # Rate limiting
                if i < total_pmids:
                    time.sleep(0.5)  # 2 requests per second max
                    
            except KeyboardInterrupt:
                print("\n⚠️ User interrupted. Saving current progress...")
                break
            except Exception as e:
                print(f"❌ Error processing PMID {pmid}: {str(e)}")
                if USE_TQDM:
                    progress_bar.update(1)
                continue
                
    finally:
        if USE_TQDM:
            progress_bar.close()
    
    print("\n" + "="*60)
    print(f"PROCESSING COMPLETE".center(60))
    print("="*60)
    print(f"Total PMIDs processed: {len(pmids):,}")
    print(f"Total links found: {len(out):,}")
    if getattr(cfg, 'europe_pmc_cc_by_only', False):
        print("Note: Only CC-BY licensed links were included")
    print("="*60)
    
    return out
    
    print(f"\nCompleted Europe PMC search. Total links: {len(out)}")
    return out