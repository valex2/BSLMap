# BSLMap Project – Architectural Vision

This project aims to build a **public-facing, interactive map of BSL-3/4 laboratories worldwide**, enriched with evidence from **scientific publications** about what pathogens and research types are associated with each facility.  

The design balances **clarity, reproducibility, and safety**: all data comes from *public sources* (PubMed, Europe PMC, Unpaywall, open metadata) and is transformed step by step into structured map-ready outputs.

---

## 🏗 Architectural Layers

### 1. **Data lake (bronze → silver → gold)**
- **Bronze:** Raw pulls, stored exactly as harvested.  
  Examples: PubMed abstracts, EuPMC links.  
- **Silver:** Normalized and chunked data, ready for LLM extraction.  
  Examples: `corpus.jsonl`, `extractions.jsonl`.  
- **Gold:** Final user-facing outputs.  
  Examples: `extracted_labs.csv`, `labs.geojson` (for the map).

This “bronze/silver/gold” model is common in data engineering and keeps provenance clear.

---

### 2. **Core logic vs orchestration**
- **Core logic (`src/bslmap/`)**: Pure, testable Python functions (e.g., `harvest_pubmed.search_pubmed`, `build_corpus.build_corpus`).  
- **CLI wrappers (`cli/`)**: Thin Typer apps that expose these functions to the command line (`python -m cli.harvest pubmed ...`).  
- **Orchestration (`Makefile`)**: Declarative workflow describing how each step depends on the previous.

This separation ensures logic can be tested in isolation, while the pipeline can be run with one command.

---

### 3. **Evidence extraction workflow**
1. **Harvest:** Query PubMed by institution + pathogen keywords.  
   - Always free to access abstracts.  
   - Optionally enrich with EuPMC/Unpaywall for open-licensed full text.  
2. **Corpus build:** Merge abstracts/full text into LLM-ready JSONL, chunked for context.  
3. **LLM extraction:** Use GPT-2 medium with dynamic prompt loading to extract labs, pathogens, BSL levels, and research types.  
   - **Model:** `gpt2-medium` for reliable structured JSON generation
   - **Prompt:** Dynamically loaded from `config/prompt.md` for easy updates
   - **Output:** Structured JSON with pathogens, research_types, evidence_spans, confidence scores
   - **Latent detection:** Model infers implicit information from biomedical text context
4. **Consolidate:** Roll up extractions to one row per publication.  
5. **Map build:** Join structured CSV with curated lab metadata → GeoJSON for interactive visualization.

---

### 4. **Frontend**
- A lightweight Leaflet.js map (`web/index.html`) reads `data/gold/labs.geojson`.  
- Popups show facility metadata plus extracted evidence counts and PMIDs.

---

### 5. **Governance guardrails**
- Data sources limited to public APIs and open-licensed text.  
- Explicit provenance preserved in every layer.  
- No operational details (staff rosters, security info, etc.) are ingested.

---

## ⚙️ Supporting Components

### **Config (TOML)**
- `config/settings.toml` holds pipeline parameters (e.g., since_year, max_per_institution, chunk size).  
- Loaded via `pydantic-settings`.  
- Can be overridden by environment variables prefixed with `BSLMAP_`.  
- Keeps all knobs centralized, reproducible, and human-readable.

### **Conda environment**
- `environment.yml` specifies Python + dependencies.  
- Run `make env` to create/update the Conda env.  
- Everything else (`make bronze`, `make silver`, etc.) uses `conda run -n bslmap …` to guarantee the right interpreter.  
- This ensures reproducibility across developer machines and CI.

### **Makefile + CLI**
- **Makefile:** Encodes the data pipeline as a set of file-based targets.  
  - `make bronze` → harvest PubMed + EuPMC → `data/bronze/...`  
  - `make silver` → build LLM corpus → `data/silver/...`  
  - `make gold` → consolidate + build map → `data/gold/...`  
  - `make all` → run bronze → silver → gold in sequence
  - `make clean` → remove all generated files
  - `make debug` → run with debug output (equivalent to `make silver DEBUG=1`)

- **CLI:** Each pipeline step is a Typer app with `--in/--out` options.  
  - Harvest:  
    ```bash
    python -m cli.harvest pubmed --institutions config/institutions.txt --keywords config/pathogen_keywords.txt --out data/bronze/pubmed_all.jsonl
    ```
  - Build corpus:
    ```bash
    python -m cli.corpus data/bronze/pubmed_all.jsonl data/bronze/eupmc_links.jsonl data/silver/corpus.jsonl
    ```
  - Extract with LLM:
    ```bash
    python -m cli.extract data/silver/corpus.jsonl data/silver/extractions.jsonl --batch-size 4
    ```
  - Consolidate extractions:
    ```bash
    python -m cli.consolidate merge data/silver/extractions.jsonl data/gold/extracted_labs.csv
    ```

### 🐛 Debugging and Troubleshooting

#### Verbose Output
Add `DEBUG=1` to any make command to enable detailed logging:
```bash
make silver DEBUG=1
```

#### Log Files
- `extract_debug.log`: Contains detailed logs from the LLM extraction process
- `harvest.log`: Logs from the data harvesting process

#### Common Issues

1. **LLM Model Performance**
   - The pipeline now uses `gpt2-medium` for reliable structured JSON extraction
   - Processing speed: ~6-7 seconds per chunk with proper GPU acceleration
   - If extraction returns only `doc_id` fields, check model loading and prompt formatting

2. **Memory Issues**
   - The LLM extraction can be memory-intensive (requires ~1GB RAM)
   - Try reducing the batch size: `--batch-size 1` or `--batch-size 2`
   - Monitor memory usage with `top` or `htop`
   - Use MPS acceleration on Apple Silicon for better performance

3. **CUDA/GPU Related Errors**
   - Pipeline supports CUDA, MPS (Apple Silicon), and CPU fallback
   - To force CPU-only mode, set `CUDA_VISIBLE_DEVICES=` in your environment
   - MPS is automatically detected and used on Apple Silicon Macs

4. **Partial Processing**
   - To process only a subset of the data, use `--max-chunks N`
   - Example: `python -m cli.extract ... --max-chunks 10`
   - Useful for testing prompt changes or debugging extraction issues

5. **Environment Issues**
   - Ensure all dependencies are installed: `conda env update -f environment.yml --prune`
   - Check Python and package versions match those in `environment.yml`
   - Verify transformers and torch versions are compatible

#### Debugging Tips

1. **Check Logs**
   ```bash
   tail -f extract_debug.log
   ```

2. **Inspect Intermediate Files**
   ```bash
   # View first few lines of a JSONL file
   head -n 5 data/silver/corpus.jsonl | jq
   
   # Count records
   wc -l data/silver/corpus.jsonl
   ```

3. **Test with a Small Dataset**
   ```bash
   # Create a test corpus with 10 chunks
   head -n 10 data/silver/corpus.jsonl > test_corpus.jsonl
   python -m cli.extract test_corpus.jsonl test_output.jsonl --batch-size 1 --max-chunks 3 --debug
   ```

4. **Validate Extraction Output**
   ```bash
   # Check if extractions contain structured data
   head -n 5 data/silver/extractions.jsonl | jq .
   
   # Count successful extractions (should have more than just doc_id)
   jq 'select(has("pathogens"))' data/silver/extractions.jsonl | wc -l
   ```

---

## 🌍 Vision
By structuring the project around **unitized layers**, **config-driven execution**, and **clean orchestration**, BSLMap aims to:

- Provide a **transparent, reproducible view** of BSL-3/4 labs worldwide.  
- Enable enrichment with **LLM-extracted evidence** while preserving provenance.  
- Stay safe, legal, and useful for researchers, policymakers, and the public.  

The architecture makes it easy to extend (e.g., add Unpaywall, add Crossref, improve alias linking) without breaking the clean pipeline structure.

## 🤖 LLM Extraction Details

The current implementation uses **GPT-2 Medium** for structured information extraction:

- **Model**: `gpt2-medium` (355M parameters)
- **Prompt**: Dynamically loaded from `config/prompt.md`
- **Output Format**: Structured JSON with fields:
  - `pathogens`: List of pathogen names mentioned
  - `research_types`: Types of research conducted
  - `evidence_spans`: Relevant text snippets supporting the extraction
  - `confidence`: Confidence score (0.0-1.0)
  - `ppp_or_gof`: Boolean indicating pathogen research classification
- **Performance**: ~6-7 seconds per document chunk
- **Capabilities**: Infers latent information from biomedical text context, not just explicit keyword matching

### Prompt Engineering

The extraction prompt can be modified in `config/prompt.md` without code changes. The current prompt:
- Uses few-shot examples to guide JSON structure
- Optimized for biomedical literature
- Focuses on BSL lab identification and pathogen research classification
- Includes confidence scoring for quality assessment