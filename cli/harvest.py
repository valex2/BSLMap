"""CLI module for harvesting BSL map data."""

import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import typer
from bslmap.cfg import Settings
from bslmap.harvest_pubmed import search_pubmed
from bslmap.harvest_eupmc import links_for_pmids
from bslmap.io_utils import write_jsonl, read_jsonl

app = typer.Typer()


@app.command()
def pubmed(institutions: Path, keywords: Path, out: Path) -> None:
    """Harvest PubMed data using institutions and keywords.
    
    Args:
        institutions: Path to institutions file
        keywords: Path to keywords file
        out: Output path for harvested data
    """
    cfg = Settings()
    insts = [x.strip() for x in institutions.read_text().splitlines() if x.strip()]
    keys = [x.strip() for x in keywords.read_text().splitlines() if x.strip()]
    records = search_pubmed(insts, keys, cfg)
    out.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(out, records)


@app.command()
def eupmc(pmids_from: Path, out: Path) -> None:
    """Harvest EUPMC data from PMIDs.
    
    Args:
        pmids_from: Path to file containing PMIDs
        out: Output path for harvested data
    """
    print(f"\n{'='*60}\nEUROPE PMC HARVESTER - DEBUG MODE\n{'='*60}")
    print(f"Input file: {pmids_from.absolute()}")
    print(f"Output file: {out.absolute()}")
    
    # Load settings
    try:
        cfg = Settings()
        print("✓ Settings loaded successfully")
    except Exception as e:
        print(f"❌ Error loading settings: {e}")
        raise
    
    # Read PMIDs
    try:
        print(f"\nReading PMIDs from: {pmids_from}")
        records = list(read_jsonl(pmids_from))
        print(f"Found {len(records)} records in input file")
        
        pmids = []
        for rec in records:
            if isinstance(rec, dict) and "pmid" in rec:
                pmids.append(str(rec["pmid"]).strip())
        
        if not pmids:
            print("❌ No valid PMIDs found in the input file")
            print("Sample of records:")
            for rec in records[:3]:
                print(f"  - {rec}")
            return
            
        print(f"✓ Found {len(pmids)} valid PMIDs")
        print(f"First 5 PMIDs: {', '.join(pmids[:5])}...")
        
    except Exception as e:
        print(f"❌ Error reading PMIDs: {e}")
        raise
    
    # Process PMIDs
    try:
        print(f"\nStarting Europe PMC harvest for {len(pmids)} PMIDs...")
        links = links_for_pmids(pmids, cfg)
        print(f"\n✓ Harvest complete. Found {len(links)} links")
        
        # Save results
        out.parent.mkdir(parents=True, exist_ok=True)
        write_jsonl(out, links)
        print(f"✓ Results saved to: {out.absolute()}")
        
    except Exception as e:
        print(f"❌ Error during harvest: {e}")
        raise


if __name__ == "__main__":
    app()