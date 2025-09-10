"""Module for extracting BSL lab information using a local LLM."""

import json
import time
import logging
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from tqdm import tqdm
from bslmap.io_utils import read_jsonl

# Configure logging
logger = logging.getLogger(__name__)

def log_memory_usage() -> None:
    """Log current memory usage."""
    try:
        import psutil
        process = psutil.Process()
        mem_info = process.memory_info()
        logger.debug(f"Memory usage: RSS={mem_info.rss / (1024**2):.2f}MB, "
                   f"VMS={mem_info.vms / (1024**2):.2f}MB")
    except Exception as e:
        logger.warning(f"Could not log memory usage: {str(e)}")

def load_model_and_tokenizer(debug: bool = False):
    """
    Load an efficient LLM and tokenizer optimized for extraction tasks.
    
    Args:
        debug: If True, print detailed debug information
        
    Returns:
        Tuple containing (model, tokenizer)
    """
    # Use a smaller causal LM that's better for structured output
    # GPT-2 medium is good for instruction following and JSON generation
    model_name = "gpt2-medium"  # Smaller, faster model for structured output
    
    if debug:
        logger.info(f"Loading model: {model_name}")
        logger.info(f"PyTorch version: {torch.__version__}")
        logger.info(f"CUDA available: {torch.cuda.is_available()}")
        log_memory_usage()
    
    try:
        start_time = time.time()
        
        if debug:
            logger.info("Loading tokenizer...")
        
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Fix padding token issue
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        if debug:
            logger.info(f"Tokenizer loaded in {time.time() - start_time:.2f}s")
            logger.info(f"Loading model with device_map='auto'...")
            log_memory_usage()
        
        # Determine best device (MPS for Mac M1/M2, CUDA for NVIDIA, CPU fallback)
        if torch.backends.mps.is_available():
            device = "mps"
            torch_dtype = torch.float16  # Use half precision for speed
        elif torch.cuda.is_available():
            device = "cuda"
            torch_dtype = torch.float16
        else:
            device = "cpu"
            torch_dtype = torch.float32
            
        if debug:
            logger.info(f"Using device: {device} with dtype: {torch_dtype}")
        
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch_dtype,
            low_cpu_mem_usage=True,
        )
        
        # Move to optimal device
        model = model.to(device)
        
        if debug:
            logger.info(f"Model loaded in {time.time() - start_time:.2f}s")
            logger.info(f"Model device: {next(model.parameters()).device}")
            log_memory_usage()
        
        return model, tokenizer
        
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error details: {str(e)}")
        if debug:
            logger.error(f"Traceback: {traceback.format_exc()}")
        raise

def load_prompt_from_config() -> str:
    """Load the extraction prompt from config/prompt.md."""
    try:
        prompt_path = Path(__file__).parent.parent.parent / "config" / "prompt.md"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        logger.warning(f"Could not load prompt from config/prompt.md: {e}")
        # Fallback prompt if config file is not available
        return """You are extracting *facility-level* biosafety metadata from biomedical literature to support a public, high-level map of BSL-3/4 labs. Use only what is explicitly stated or reasonably inferable from the text.

Return one JSON object per input CHUNK, following this schema (omit fields you cannot support):

{
  "doc_id": "<copy from input>",
  "lab_name": "<facility name if explicitly named>",
  "institution": "<org operating the lab (e.g., UTMB, Inserm)>",
  "country": "<country>",
  "city": "<city or region>",
  "bsl_level_inferred": "<BSL-3|BSL-4|unknown>",
  "pathogens": ["Ebola","Nipah","H5N1"],
  "research_types": ["challenge study","neutralization assay","virus isolation","reverse genetics"],
  "ppp_or_gof": true/false,
  "confidence": 0.0-1.0,
  "evidence_spans": ["short quotes that justify the fields"],
  "source_pmid": "<digits>"
}

Rules:
- Prefer explicit mentions. If multiple labs are mentioned, choose the one tied to the *methods* or *facilities* used.
- Do not include operational details (floorplans, shift times, staff rosters).
- If the chunk is too vague, return only {"doc_id": "..."}."""

def format_prompt(chunk: Dict[str, Any], base_prompt: str) -> str:
    """
    Format the extraction prompt with document information for causal LMs.
    
    Args:
        chunk: Document chunk with metadata
        base_prompt: Base prompt template
        
    Returns:
        Formatted prompt string optimized for GPT-style models
    """
    # Extract metadata
    text = chunk.get("text", "")[:800]  # Limit text length
    
    # Create a GPT-optimized prompt with examples
    formatted_prompt = f"""Extract BSL lab information from biomedical text and return valid JSON.

Example:
Text: "We conducted experiments with SARS-CoV-2 in our BSL-3 facility at Johns Hopkins."
JSON: {{"pathogens": ["SARS-CoV-2"], "research_types": ["experimental"], "evidence_spans": ["experiments with SARS-CoV-2 in our BSL-3 facility"], "confidence": 0.9, "ppp_or_gof": false}}

Text: {text}
JSON:"""
    
    return formatted_prompt

def extract_from_chunk(
    chunk: Dict[str, Any], 
    model, 
    tokenizer, 
    base_prompt: str,
    max_new_tokens: int = 512
) -> Dict[str, Any]:
    """Extract information from a single chunk of text using LLM."""
    try:
        # Format the prompt
        prompt = format_prompt(chunk, base_prompt)
        
        # Tokenize input with reduced max length for speed
        inputs = tokenizer(
            prompt,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=1024,  # Reduced from 2048 for faster processing
            return_token_type_ids=False
        ).to(model.device)
        
        # Generate response with GPT-specific parameters for structured output
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=200,  # Enough for JSON output
                do_sample=True,      # Use sampling for creativity
                temperature=0.3,     # Low temperature for consistency
                top_p=0.9,          # Nucleus sampling
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id
            )
        
        # Decode and parse response
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract only the generated part (remove the input prompt)
        prompt_length = len(tokenizer.decode(inputs['input_ids'][0], skip_special_tokens=True))
        if len(response) > prompt_length:
            response = response[prompt_length:].strip()
        
        # Extract JSON part from the response more robustly
        json_start = response.find('{')
        if json_start == -1:
            # Try to find JSON after "JSON:" marker
            json_marker = response.find('JSON:')
            if json_marker != -1:
                json_start = response.find('{', json_marker)
        
        if json_start == -1:
            return {"doc_id": chunk.get("doc_id", "")}
        
        # Find the matching closing brace
        brace_count = 0
        json_end = json_start
        for i, char in enumerate(response[json_start:], json_start):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    json_end = i + 1
                    break
        
        if json_end == json_start:
            return {"doc_id": chunk.get("doc_id", "")}
            
        json_str = response[json_start:json_end]
        
        try:
            result = json.loads(json_str)
            
            # Ensure doc_id is preserved
            result["doc_id"] = chunk.get("doc_id", "")
            
            # Extract PMID from doc_id if source_pmid is missing
            if "source_pmid" not in result or not result["source_pmid"]:
                doc_id = chunk.get("doc_id", "")
                if "pmid:" in doc_id:
                    pmid = doc_id.split("pmid:")[1].split("#")[0]
                    result["source_pmid"] = pmid
            
            # Ensure required fields exist with proper defaults
            if "pathogens" not in result:
                result["pathogens"] = []
            if "research_types" not in result:
                result["research_types"] = []
            if "evidence_spans" not in result:
                result["evidence_spans"] = []
            if "confidence" not in result:
                result["confidence"] = 0.5
            if "ppp_or_gof" not in result:
                result["ppp_or_gof"] = False
                
            return result
            
        except json.JSONDecodeError as e:
            print(f"JSON decode error for {chunk.get('doc_id', 'unknown')}: {e}")
            print(f"Attempted to parse: {json_str[:200]}...")
            print(f"Full response: {response[:500]}...")
            return {"doc_id": chunk.get("doc_id", "")}
            
    except Exception as e:
        print(f"LLM extraction error for {chunk.get('doc_id', 'unknown')}: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return {"doc_id": chunk.get("doc_id", "")}

def process_batch(batch: List[Dict[str, Any]], model, tokenizer, base_prompt: str, debug: bool = False) -> List[Dict[str, Any]]:
    """
    Process a batch of text chunks through the LLM extraction pipeline.
    
    Args:
        batch: List of document chunks to process
        model: Loaded LLM model
        tokenizer: Tokenizer for the model
        debug: If True, enable debug logging
        
    Returns:
        List of processed results
    """
    if debug:
        logger.info(f"Processing batch of {len(batch)} chunks")
        log_memory_usage()
    
    results = []
    
    for i, chunk in enumerate(batch, 1):
        chunk_id = chunk.get("doc_id", f"chunk-{i}")
        
        if debug:
            logger.debug(f"Processing {chunk_id}")
            
        try:
            start_time = time.time()
            result = extract_from_chunk(chunk, model, tokenizer, base_prompt)
            
            if debug:
                process_time = time.time() - start_time
                logger.debug(f"Processed {chunk_id} in {process_time:.2f}s")
                
            results.append(result)
            
        except Exception as e:
            logger.error(f"Error processing {chunk_id}: {str(e)}")
            if debug:
                logger.error(f"Error details for {chunk_id}: {traceback.format_exc()}")
            
            # Add an error result for failed chunks
            results.append({
                "doc_id": chunk_id,
                "error": str(e),
                "success": False
            })
    
    if debug:
        success_count = sum(1 for r in results if r.get("success", True))
        logger.info(f"Batch completed: {success_count}/{len(batch)} chunks processed successfully")
    
    return results

def process_corpus(
    input_path: Path,
    output_path: Path,
    batch_size: int = 4,
    max_chunks: Optional[int] = None,
    debug: bool = False
) -> None:
    """
    Process the corpus file and extract BSL lab information using a local LLM.
    
    Args:
        input_path: Path to the input JSONL corpus file
        output_path: Path to write the output JSONL file
        batch_size: Number of chunks to process in each batch
        max_chunks: Maximum number of chunks to process (for testing)
        debug: If True, enable debug logging
    """
    logger.info(f"Starting corpus processing: {input_path}")
    start_time = time.time()
    
    try:
        # Log initial memory usage
        if debug:
            log_memory_usage()
        
        # Load the prompt from config
        logger.info("Loading extraction prompt from config/prompt.md...")
        base_prompt = load_prompt_from_config()
        
        # Load model and tokenizer
        model_load_start = time.time()
        logger.info("Loading model and tokenizer...")
        model, tokenizer = load_model_and_tokenizer(debug=debug)
        logger.info(f"Model and tokenizer loaded in {time.time() - model_load_start:.2f}s")
        
        # Read the corpus
        logger.info(f"Reading corpus from {input_path}...")
        corpus = list(read_jsonl(input_path))
        
        if not corpus:
            logger.warning("No documents found in the corpus")
            return
            
        if max_chunks:
            logger.info(f"Limiting processing to {max_chunks} chunks")
            corpus = corpus[:max_chunks]
        
        logger.info(f"Processing {len(corpus)} chunks in batches of {batch_size}")
        
        # Process in batches
        results = []
        total_chunks = len(corpus)
        
        with tqdm(total=total_chunks, desc="Processing chunks") as pbar:
            for i in range(0, total_chunks, batch_size):
                batch = corpus[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (total_chunks + batch_size - 1) // batch_size
                
                if debug:
                    logger.info(f"\nProcessing batch {batch_num}/{total_batches} "
                              f"(chunks {i+1}-{min(i+batch_size, total_chunks)}/{total_chunks})")
                    log_memory_usage()
                
                try:
                    batch_start = time.time()
                    batch_results = process_batch(batch, model, tokenizer, base_prompt, debug=debug)
                    results.extend(batch_results)
                    
                    if debug:
                        batch_time = time.time() - batch_start
                        logger.info(f"Batch {batch_num} completed in {batch_time:.2f}s")
                        logger.info(f"Current results count: {len(results)}")
                        
                except Exception as e:
                    logger.error(f"Error processing batch {batch_num}: {str(e)}")
                    if debug:
                        logger.error(f"Batch error details: {traceback.format_exc()}")
                    # Continue with next batch
                    continue
                    
                pbar.update(len(batch))
        
        # Write results
        logger.info(f"Writing {len(results)} results to {output_path}")
        with open(output_path, 'w') as f:
            for result in results:
                f.write(json.dumps(result) + '\n')
        
        logger.info(f"Processing completed in {time.time() - start_time:.2f} seconds")
        
    except Exception as e:
        logger.error(f"Fatal error in process_corpus: {str(e)}")
        if debug:
            logger.error(f"Error details: {traceback.format_exc()}")
        raise
    
    print(f"Saved extractions to {output_path}")
