# BSLMap Project – Interactive BSL-3/4 Laboratory Mapper

## Quick Links

- **Application**: [http://localhost:3003](http://localhost:3003) (when running locally)
- **API Documentation**: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
- **Backend API**: [http://localhost:8000](http://localhost:8000)

## Project Overview

This project aims to build a public-facing, interactive map of BSL-3/4 laboratories worldwide, enriched with evidence from scientific publications about what pathogens and research types are associated with each facility.

This project aims to build a public-facing, interactive map of BSL-3/4 laboratories worldwide, enriched with evidence from scientific publications about what pathogens and research types are associated with each facility.

The design balances clarity, reproducibility, and safety: all data comes from public sources (PubMed, Europe PMC, Unpaywall, open metadata) and is transformed step by step into structured map-ready outputs.

⸻

🏗 Architectural Layers

1. Data lake (bronze → silver → gold)
	•	Bronze: Raw pulls, stored exactly as harvested.
Examples: PubMed abstracts, EuPMC links.
	•	Silver: Normalized and chunked data, ready for LLM extraction.
Examples: corpus.jsonl (contains institution info), extractions.jsonl.
	•	Gold: Final user-facing outputs with institution metadata.
Examples: extracted_labs.csv, labs.geojson (for the map).

This “bronze/silver/gold” model is common in data engineering and maintains clear data lineage and provenance.

⸻

2. Core logic vs orchestration
	•	Core logic (src/bslmap/): Pure, testable Python functions (e.g., harvest_pubmed.search_pubmed, build_corpus.build_corpus).
	•	CLI wrappers (cli/): Thin Typer apps that expose these functions to the command line (python -m cli.harvest pubmed ...).
	•	Orchestration (Makefile): Declarative workflow describing how each step depends on the previous.

This separation ensures logic can be tested in isolation, while the pipeline can be run with one command.

⸻

3. Evidence Extraction and Lab Data Pipeline

The pipeline processes data through these key stages:
	1.	Harvest
	•	Query PubMed by institution + pathogen keywords
	•	Optionally enrich with EuPMC/Unpaywall for open-licensed full text
	•	Output: Raw data in data/bronze/
	2.	Corpus Build
	•	Merge abstracts/full text into LLM-ready JSONL format
	•	Chunk content for optimal context handling
	•	Output: data/silver/corpus.jsonl
	3.	LLM Extraction
	•	Use GPT-2 medium for structured data extraction
	•	Extract labs, pathogens, BSL levels, and research types
	•	Preserve institution information from the original corpus
	•	Output: data/silver/extractions.jsonl
	•	Key Features:
	•	Dynamic prompt loading from config/prompt.md
	•	Structured JSON output with confidence scoring
	•	Latent information inference from biomedical context
	•	Institution information preservation from original sources
	4.	Consolidate Evidence
	•	Roll up extractions to one row per publication
	•	Enrich with institution metadata from the corpus
	•	Match with geocoded lab data when available
	•	Output: data/gold/extracted_labs.csv with complete institution info
	5.	Lab Metadata Processing
	•	Inputs:
	•	config/institutions.txt (list of lab names)
	•	Institution information from PubMed records
	•	Process:
	1.	Geocode each institution using OpenStreetMap’s Nominatim
	2.	Cache results in data/labs.csv to avoid repeated geocoding
	3.	Preserve original institution information from publications
	•	Output: data/labs.csv with columns:
	•	institution: Full institution name
	•	latitude, longitude: Geographic coordinates
	•	city, country: Location details
	•	Data Flow:
	•	Institution information is preserved throughout the pipeline
	•	Original institution names from publications are prioritized
	•	Geocoding provides consistent location data
	6.	Map Generation
	•	Join extracted evidence with lab metadata
	•	Generate GeoJSON for interactive visualization
	•	Output: data/gold/labs.geojson

⸻

4. Web Interface (Next-Generation Strategy)

The initial prototype (Flask + Leaflet) demonstrated feasibility but is limited in scalability and interactivity. The next-generation web interface is designed as a robust, API-driven system:

🔹 Core Principles
	•	API-first backend: Serve lab and evidence data as JSON endpoints.
	•	Reactive frontend: Modern framework (React, Vue, or Svelte) for filtering and exploration.
	•	Efficient map rendering: MapLibre GL (open-source Mapbox) with clustering and vector tiles.
	•	Responsive, mobile-first UI: Optimized for researchers and policymakers accessing via phones/tablets.
	•	Progressive enhancement: Flask/FastAPI can remain as a lightweight backend, with frontend decoupled.

🔹 Implementation

Backend (data + API)
	•	Serve labs.geojson and evidence CSVs via FastAPI/Flask REST.
	•	Example endpoints:
	•	/labs → all labs with metadata
	•	/labs/{id} → details + evidence
	•	/pathogens → pathogen taxonomy for filtering
	•	/search?q=... → text search

## Development Setup

### Prerequisites

- Python 3.9+
- Node.js 16+
- Conda (recommended for Python environment management)

### Environment Setup

1. **Create and activate conda environment**:
   ```bash
   conda env create -f environment.yml
   conda activate bslmap
   ```

2. **Install Python dependencies**:
   ```bash
   make install
   ```

3. **Install frontend dependencies**:
   ```bash
   make web-install
   ```

### Running the Application

1. **Start the backend server**:
   ```bash
   make backend
   ```

2. **Start the frontend development server**:
   ```bash
   make frontend
   ```

   Or run both together:
   ```bash
   make web
   ```

## Frontend (Interactive Client)
- Built with React + Vite
- MapLibre GL integration for performant map rendering
- UI Components:
  - Search bar (by institution, pathogen, country)
	•	Filters (BSL level, pathogen type, research type)
	•	Sidebar detail panel with evidence and publication links
	•	Mobile-friendly collapsible panels

Deployment
	•	Backend and frontend containerized separately.
	•	Frontend can be served statically (GitHub Pages/Netlify) with API hosted elsewhere.
	•	CI/CD with GitHub Actions for auto-deploying builds and API docs.

🔹 Benefits
	•	Performance: Smooth rendering even with large datasets.
	•	Scalability: Easy to add new data sources and features.
	•	Extensibility: Modular architecture supports future analytics or timeline visualizations.
	•	User Experience: Modern design with intuitive filtering and evidence browsing.

⸻

5. Governance guardrails
	•	Data sources limited to public APIs and open-licensed text.
	•	Explicit provenance preserved in every layer.
	•	No operational details (staff rosters, security info, etc.) are ingested.

⸻

⚙️ Supporting Components

(unchanged from your version — config, conda, Makefile, CLI, debugging, etc.)

⸻

🌍 Vision

By structuring the project around unitized layers, config-driven execution, and clean orchestration, BSLMap aims to:
	•	Provide a transparent, reproducible view of BSL-3/4 labs worldwide.
	•	Enable enrichment with LLM-extracted evidence while preserving provenance.
	•	Stay safe, legal, and useful for researchers, policymakers, and the public.

The architecture makes it easy to extend (e.g., add Unpaywall, add Crossref, improve alias linking) without breaking the clean pipeline structure.