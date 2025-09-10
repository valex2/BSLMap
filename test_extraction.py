#!/usr/bin/env python3
"""Test script to debug LLM extraction issues."""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from bslmap.extract_with_llm import load_model_and_tokenizer, extract_from_chunk

def test_single_chunk():
    """Test extraction on a single chunk."""
    
    # Sample chunk from the corpus
    test_chunk = {
        "doc_id": "pmid:40924481#chunk0",
        "source": "pubmed",
        "title": "A multi-omics recovery factor predicts long COVID in the IMPACC study.",
        "aff_hint": "National Institute of Allergy and Infectious Diseases",
        "text": "Following SARS-CoV-2 infection, ~10-35% of COVID-19 patients experience long COVID (LC), in which debilitating symptoms persist for at least three months. Elucidating biologic underpinnings of LC could identify therapeutic opportunities. We utilized machine learning methods on biologic analytes provided over 12-months after hospital discharge from >500 COVID-19 patients in the IMPACC cohort to identify a multi-omics \"recovery factor\", trained on patient-reported physical function survey scores. Immune profiling data included PBMC transcriptomics, serum O-link and plasma proteomics, plasma metabolomics, and blood CyTOF protein levels."
    }
    
    print("Loading model and tokenizer...")
    try:
        model, tokenizer = load_model_and_tokenizer(debug=True)
        print("Model loaded successfully!")
        
        print("\nTesting extraction...")
        result = extract_from_chunk(test_chunk, model, tokenizer)
        
        print("\nExtraction result:")
        print(json.dumps(result, indent=2))
        
        return result
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_single_chunk()
