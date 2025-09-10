"""CLI module for consolidating BSL map extractions."""

import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import typer
from bslmap.consolidate_extractions import merge_extractions

app = typer.Typer()


@app.command()
def merge(in_: Path, out: Path) -> None:
    """Merge extraction files from input path to output path.
    
    Args:
        in_: Input path containing extraction files
        out: Output path for merged results
    """
    out.parent.mkdir(parents=True, exist_ok=True)
    merge_extractions(in_, out)


if __name__ == "__main__":
    app()