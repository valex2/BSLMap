import json
from enum import StrEnum
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Query, HTTPException
from geojson_pydantic import FeatureCollection
from pydantic import BaseModel, Field

router = APIRouter()

# Paths - Go up 3 levels from current file to reach project root
BASE_DIR = Path(__file__).parent.parent.parent.parent.parent
GEOJSON_PATH = BASE_DIR / 'data' / 'gold' / 'labs.geojson'
print(f"Looking for GeoJSON file at: {GEOJSON_PATH}")
print(f"File exists: {GEOJSON_PATH.exists()}")

class BSLLevel(StrEnum):
    BSL2 = "BSL-2"
    BSL3 = "BSL-3"
    BSL4 = "BSL-4"
    UNKNOWN = "Unknown"

class LabFilters(BaseModel):
    bsl_level: Optional[BSLLevel] = Field(None, description="Filter by BSL level")
    country: Optional[str] = Field(None, description="Filter by country")
    pathogen: Optional[str] = Field(None, description="Filter by pathogen")
    research_type: Optional[str] = Field(None, description="Filter by type of research")

@router.get("/labs")
async def get_labs(
    bsl_level: Optional[str] = Query(None, description="Filter by BSL level"),
    country: Optional[str] = Query(None, description="Filter by country"),
    pathogen: Optional[str] = Query(None, description="Filter by pathogen"),
    research_type: Optional[str] = Query(None, description="Filter by type of research")
):
    """
    Get all labs with optional filtering.
    Returns GeoJSON FeatureCollection of lab locations and metadata.
    """
    print(f"Loading labs from: {GEOJSON_PATH}")
    print(f"File exists: {GEOJSON_PATH.exists()}")
    
    try:
        with open(GEOJSON_PATH, 'r') as f:
            data = json.load(f)
        
        print(f"Loaded {len(data.get('features', []))} labs")
        
        features = data.get('features', [])
        
        # Apply filters
        filtered_features = []
        for feature in features:
            properties = feature.get('properties', {})
            
            # Skip if any filter doesn't match
            if bsl_level and properties.get('bsl_level') != bsl_level:
                continue
            if country and properties.get('country', '').lower() != country.lower():
                continue
            if pathogen and not any(
                p.lower() == pathogen.lower() 
                for p in properties.get('pathogens', [])
            ):
                continue
            if research_type and not any(
                r.lower() == research_type.lower() 
                for r in properties.get('research_types', [])
            ):
                continue
                
            filtered_features.append(feature)
        
        response = {
            "type": "FeatureCollection",
            "features": filtered_features
        }
        
        print(f"Returning {len(filtered_features)} labs after filtering")
        return response
        
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error decoding JSON data: {str(e)}"
        )
    except FileNotFoundError:
        print(f"File not found: {GEOJSON_PATH}")
        raise HTTPException(
            status_code=404,
            detail="Lab data file not found"
        )
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error loading lab data: {str(e)}"
        )

@router.get("/labs/{lab_id}")
async def get_lab(lab_id: str):
    """
    Get detailed information about a specific lab by ID.
    """
    try:
        with open(GEOJSON_PATH, 'r') as f:
            data = json.load(f)
        
        for feature in data.get('features', []):
            if feature.get('id') == lab_id:
                return feature
        
        raise HTTPException(status_code=404, detail="Lab not found")
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading lab data: {str(e)}"
        )

@router.get("/pathogens")
async def get_pathogens():
    """
    Get a list of all unique pathogens across all labs.
    """
    try:
        with open(GEOJSON_PATH, 'r') as f:
            data = json.load(f)
        
        pathogens = set()
        for feature in data.get('features', []):
            pathogens.update(feature.get('properties', {}).get('pathogens', []))
        
        return sorted(list(pathogens))
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading pathogen data: {str(e)}"
        )

@router.get("/research-types")
async def get_research_types():
    """
    Get a list of all unique research types across all labs.
    """
    try:
        with open(GEOJSON_PATH, 'r') as f:
            data = json.load(f)
        
        research_types = set()
        for feature in data.get('features', []):
            research_types.update(feature.get('properties', {}).get('research_types', []))
        
        return sorted(list(research_types))
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading research type data: {str(e)}"
        )
