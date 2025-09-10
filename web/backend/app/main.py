import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

# Initialize FastAPI app
app = FastAPI(
    title="BSLMap API",
    description="API for BSL-3/4 laboratory mapping project",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3003", "http://127.0.0.1:3003"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

# Paths
BASE_DIR = Path(__file__).parent.parent.parent.parent
GEOJSON_PATH = BASE_DIR / 'data' / 'gold' / 'labs.geojson'

# Cache for lab data
_labs_data = None

def get_labs_data() -> dict:
    """Load and cache the labs GeoJSON data."""
    global _labs_data
    
    if _labs_data is None:
        try:
            with open(GEOJSON_PATH, 'r') as f:
                _labs_data = json.load(f)
        except Exception as e:
            print(f"Error loading labs data: {e}")
            _labs_data = {
                "type": "FeatureCollection",
                "features": []
            }
    
    return _labs_data

# Import routers
from app.routers import labs

# Include routers with /api prefix
app.include_router(labs.router, prefix="/api")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers and monitoring."""
    return {"status": "healthy"}

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "BSLMap API",
        "version": "0.1.0",
        "docs": "/api/docs",
        "endpoints": [
            "/api/labs",
            "/api/labs/{lab_id}",
            "/api/pathogens",
            "/api/research-types"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
