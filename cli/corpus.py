"""CLI module for building BSL map corpus."""

import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import typer
from bslmap.build_corpus import build_corpus

app = typer.Typer()


@app.command()
def build(pubmed: Path, eupmc: Path, out: Path) -> None:
    """Build corpus from PubMed and EUPMC data.
    
    Args:
        pubmed: Path to PubMed data
        eupmc: Path to EUPMC data
        out: Output path for corpus
    """
    out.parent.mkdir(parents=True, exist_ok=True)
    build_corpus(pubmed, eupmc, out)


if __name__ == "__main__":
    app()