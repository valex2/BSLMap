"""CLI module for extracting BSL lab information using LLM."""

import sys
import os
import time
from pathlib import Path
import logging
from typing import Optional

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import typer
from bslmap.extract_with_llm import process_corpus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('extract_debug.log')
    ]
)
logger = logging.getLogger(__name__)

def print_section_header(title: str) -> None:
    """Print a formatted section header."""
    logger.info("\n" + "=" * 80)
    logger.info(f" {title}")
    logger.info("=" * 80)

def print_debug_info() -> None:
    """Print debug information about the environment."""
    try:
        import torch
        import platform
        import psutil
        
        print_section_header("DEBUG INFORMATION")
        
        # System info
        logger.info("System Information:")
        logger.info(f"  - System: {platform.system()} {platform.release()}")
        logger.info(f"  - Processor: {platform.processor()}")
        logger.info(f"  - Python: {sys.executable}")
        logger.info(f"  - Python Version: {platform.python_version()}")
        
        # Memory info
        mem = psutil.virtual_memory()
        logger.info("\nMemory Information:")
        logger.info(f"  - Total: {mem.total / (1024**3):.2f} GB")
        logger.info(f"  - Available: {mem.available / (1024**3):.2f} GB")
        logger.info(f"  - Used: {mem.used / (1024**3):.2f} GB")
        logger.info(f"  - Free: {mem.free / (1024**3):.2f} GB")
        
        # PyTorch info
        logger.info("\nPyTorch Information:")
        logger.info(f"  - Version: {torch.__version__}")
        logger.info(f"  - CUDA Available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            logger.info(f"  - CUDA Version: {torch.version.cuda}")
            logger.info(f"  - GPU: {torch.cuda.get_device_name(0)}")
        
        # Environment variables
        logger.info("\nEnvironment Variables:")
        for var in ['CONDA_DEFAULT_ENV', 'CUDA_VISIBLE_DEVICES', 'LD_LIBRARY_PATH']:
            logger.info(f"  - {var}: {os.environ.get(var, 'Not set')}")
            
    except Exception as e:
        logger.error(f"Error gathering debug info: {str(e)}")

app = typer.Typer()

@app.command()
def extract(
    input_path: Path = typer.Argument(..., help="Path to the input corpus file"),
    output_path: Path = typer.Argument(..., help="Path to save the extractions"),
    batch_size: int = typer.Option(4, "--batch-size", "-b", help="Batch size for processing"),
    max_chunks: Optional[int] = typer.Option(None, "--max-chunks", "-m", help="Maximum number of chunks to process"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug output"),
) -> None:
    """Extract BSL lab information from a corpus using a local LLM."""
    start_time = time.time()
    
    # Set log level
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        print_debug_info()
    
    # Log start of extraction
    logger.info(f"Starting extraction at {time.ctime()}")
    logger.info(f"Input file: {input_path}")
    logger.info(f"Output file: {output_path}")
    logger.info(f"Batch size: {batch_size}")
    logger.info(f"Extraction method: LLM-based with prompt from config/prompt.md")
    if max_chunks:
        logger.info(f"Max chunks: {max_chunks}")
    
    try:
        process_corpus(
            input_path=input_path,
            output_path=output_path,
            batch_size=batch_size,
            max_chunks=max_chunks,
            debug=debug
        )
        elapsed = time.time() - start_time
        logger.info(f"\nExtraction completed successfully in {elapsed:.2f} seconds")
    except Exception as e:
        logger.error(f"Extraction failed after {time.time() - start_time:.2f} seconds")
        logger.error(f"Error: {str(e)}", exc_info=True)
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
