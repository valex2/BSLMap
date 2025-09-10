"""CLI module for building BSL map GeoJSON."""

import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import typer
from bslmap.geojson import build_geojson

app = typer.Typer()


@app.command()
def build(labs: Path, evidence: Path, out: Path) -> None:
    """Build GeoJSON from labs and evidence data.
    
    Args:
        labs: Path to labs data
        evidence: Path to evidence data
        out: Output path for GeoJSON
    """
    out.parent.mkdir(parents=True, exist_ok=True)
    build_geojson(labs, evidence, out)


if __name__ == "__main__":
    app()