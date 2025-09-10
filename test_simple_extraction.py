#!/usr/bin/env python3
"""Test simple rule-based extraction as fallback."""

import json
import re
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from bslmap.io_utils import read_jsonl

def simple_rule_based_extraction(chunk):
    """Simple rule-based extraction as fallback."""
    result = {"doc_id": chunk.get("doc_id", "")}
    
    text = chunk.get("text", "").lower()
    title = chunk.get("title", "").lower()
    aff_hint = chunk.get("aff_hint", "")
    
    # Extract PMID
    doc_id = chunk.get("doc_id", "")
    if "pmid:" in doc_id:
        pmid = doc_id.split("pmid:")[1].split("#")[0]
        result["source_pmid"] = pmid
    
    # Extract institution from affiliation hint
    if aff_hint:
        result["institution"] = aff_hint
    
    # Look for BSL mentions
    bsl_patterns = [
        r"bsl-?(\d+)",
        r"biosafety level (\d+)",
        r"containment level (\d+)"
    ]
    
    for pattern in bsl_patterns:
        matches = re.findall(pattern, text + " " + title)
        if matches:
            levels = [int(m) for m in matches if m.isdigit()]
            if any(level >= 3 for level in levels):
                max_level = max(levels)
                result["bsl_level_inferred"] = f"BSL-{max_level}"
                break
    else:
        result["bsl_level_inferred"] = "unknown"
    
    # Look for common pathogens
    pathogen_keywords = [
        "ebola", "marburg", "nipah", "hendra", "sars", "mers", "covid",
        "h5n1", "h7n9", "influenza", "anthrax", "smallpox", "variola",
        "francisella", "yersinia pestis", "bacillus anthracis"
    ]
    
    found_pathogens = []
    for pathogen in pathogen_keywords:
        if pathogen in text or pathogen in title:
            found_pathogens.append(pathogen.title())
    
    result["pathogens"] = found_pathogens
    
    # Look for research types
    research_keywords = [
        "challenge study", "neutralization", "virus isolation", 
        "reverse genetics", "vaccine", "antiviral", "therapeutic"
    ]
    
    found_research = []
    for research in research_keywords:
        if research in text or research in title:
            found_research.append(research)
    
    result["research_types"] = found_research
    
    # Set defaults
    result["ppp_or_gof"] = False
    result["confidence"] = 0.3  # Lower confidence for rule-based
    result["evidence_spans"] = []
    
    return result

def test_simple_extraction():
    """Test simple extraction on a few chunks."""
    
    # Read first few chunks from corpus
    corpus_path = Path("data/silver/corpus.jsonl")
    if not corpus_path.exists():
        print("Corpus file not found")
        return
    
    chunks = list(read_jsonl(corpus_path))[:5]
    
    print(f"Testing simple extraction on {len(chunks)} chunks...")
    
    for chunk in chunks:
        result = simple_rule_based_extraction(chunk)
        print(f"\nChunk: {chunk['doc_id']}")
        print(f"Title: {chunk.get('title', '')[:100]}...")
        print(f"Result: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    test_simple_extraction()
