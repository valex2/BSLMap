"""CLI module for consolidating BSL map extractions."""

import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import typer
from bslmap.consolidate_extractions import merge_extractions

app = typer.Typer()


@app.command()
def merge(in_: Path, out: Path, corpus: Path = Path("data/silver/corpus.jsonl")) -> None:
    """Merge extraction files from input path to output path.
    
    Args:
        in_: Input path containing extraction files
        out: Output path for merged results
        corpus: Path to corpus JSONL file with original data
    """
    out.parent.mkdir(parents=True, exist_ok=True)
    merge_extractions(in_, out, corpus)


if __name__ == "__main__":
    app()