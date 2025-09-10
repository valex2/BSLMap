#!/usr/bin/env python3
"""
Script to generate labs.csv from institutions.txt with geocoding.
"""
import csv
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple
import requests
from tqdm import tqdm

def geocode_institution(name: str, country: str = '') -> Optional[Tuple[float, float, str, str]]:
    """Geocode an institution name to get its coordinates and location details."""
    base_url = "https://nominatim.openstreetmap.org/search"
    query = f"{name}, {country}" if country else name
    
    headers = {
        'User-Agent': 'BSLMap/1.0 (https://github.com/yourusername/bslmap; your.email@example.com)'
    }
    
    try:
        response = requests.get(
            base_url,
            params={
                'q': query,
                'format': 'json',
                'limit': 1,
                'addressdetails': 1
            },
            headers=headers
        )
        response.raise_for_status()
        
        data = response.json()
        if not data:
            return None
            
        result = data[0]
        lat = float(result['lat'])
        lon = float(result['lon'])
        
        # Extract city and country from address details if available
        address = result.get('address', {})
        city = address.get('city') or address.get('town') or address.get('village') or ''
        country_code = address.get('country_code', '').upper()
        
        return (lat, lon, city, country_code)
        
    except Exception as e:
        print(f"Error geocoding {name}: {str(e)}", file=sys.stderr)
        return None

def load_existing_labs(csv_path: Path) -> Dict[str, Dict]:
    """Load existing labs from CSV to avoid re-geocoding."""
    if not csv_path.exists():
        return {}
        
    labs = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            labs[row['institution']] = row
    return labs

def generate_labs_csv(institutions_path: Path, output_path: Path):
    """Generate or update labs.csv from institutions.txt."""
    # Load existing labs to avoid re-geocoding
    existing_labs = load_existing_labs(output_path)
    
    # Read institutions
    with open(institutions_path, 'r', encoding='utf-8') as f:
        institutions = [line.strip() for line in f if line.strip()]
    
    # Prepare data for CSV
    fieldnames = ['institution', 'latitude', 'longitude', 'country', 'city']
    rows = []
    
    # Process each institution
    for institution in tqdm(institutions, desc="Processing institutions"):
        if institution in existing_labs:
            rows.append(existing_labs[institution])
            continue
            
        # Try to geocode with and without country
        result = geocode_institution(institution)
        if not result:
            print(f"Warning: Could not geocode {institution}", file=sys.stderr)
            continue
            
        lat, lon, city, country = result
        rows.append({
            'institution': institution,
            'latitude': lat,
            'longitude': lon,
            'country': country,
            'city': city
        })
    
    # Write to CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"Generated {len(rows)} lab entries in {output_path}")

if __name__ == "__main__":
    # Define paths
    project_root = Path(__file__).parent.parent
    institutions_path = project_root / "config" / "institutions.txt"
    output_path = project_root / "data" / "labs.csv"
    
    generate_labs_csv(institutions_path, output_path)
