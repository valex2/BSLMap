# ---- Config ----
CONDA_ENV ?= bslmap
DEBUG ?= 0
SHELL := /bin/bash

# Set Python command with debug environment if needed
PY_ENV = PYTHONUNBUFFERED=1 PYTHONIOENCODING=UTF-8
ifneq ($(DEBUG),0)
    PY_ENV += PYTHONPATH=$(PWD)/src DEBUG=1
endif

# Use conda activation instead of conda run to avoid hanging
PY = $(PY_ENV) conda run -n $(CONDA_ENV) python
PIP = $(PY_ENV) conda run -n $(CONDA_ENV) python -m pip

# Paths
BRONZE = data/bronze
SILVER = data/silver
GOLD   = data/gold

INST   = config/institutions.txt
KEYS   = config/pathogen_keywords.txt
SETT   = config/settings.toml

# Artifacts
PUBMED_JSONL = $(BRONZE)/pubmed_all.jsonl
EUPMC_JSONL  = $(BRONZE)/eupmc_links.jsonl
CORPUS_JSONL = $(SILVER)/corpus.jsonl
EXTRACTS_JL  = $(SILVER)/extractions.jsonl     # produced by your LLM step
EXTRACTS_CSV = $(GOLD)/extracted_labs.csv
LABS_CSV     = data/labs.csv
LABS_GEOJSON = $(GOLD)/labs.geojson

.PHONY: help env install lint type test clean bronze silver gold web web-install

help:
	@echo "make env        # create/update conda env ($(CONDA_ENV))"
	@echo "make install    # install package in editable mode"
	@echo "make bronze     # PubMed/EuPMC pulls -> bronze (DEBUG=1 for verbose)"
	@echo "make silver     # corpus build -> silver (DEBUG=1 for verbose)"
	@echo "make gold       # consolidate + geojson -> gold (DEBUG=1 for verbose)"
	@echo "make debug      # run silver step with debug output (same as make silver DEBUG=1)"
	@echo "make web        # Run the web server"
	@echo "make web-install # install web dependencies"
	@echo "make lint type test clean"

env:
	conda env update -f environment.yml --prune

install:
	$(PIP) install -e ".[dev]"

lint:
	$(PY) -m ruff check .
	$(PY) -m black --check .

type:
	$(PY) -m mypy src

test:
	$(PY) -m pytest -q

clean:
	rm -rf $(BRONZE)/* $(SILVER)/* $(GOLD)/* *.log

# --- Pipeline targets ---
bronze: $(PUBMED_JSONL) $(EUPMC_JSONL)
	@echo "[$(shell date +'%Y-%m-%d %H:%M:%S')] Completed bronze target"

$(PUBMED_JSONL): $(INST) $(KEYS) $(SETT)
	@echo "[$(shell date +'%Y-%m-%d %H:%M:%S')] Starting PubMed data harvest..."
	@echo "  - Input files: $(INST), $(KEYS), $(SETT)"
	@echo "  - Output file: $@"
	@if [ "$(DEBUG)" != "0" ]; then \
		echo "  - Debug mode: enabled"; \
	fi
	@mkdir -p $(BRONZE)
	@if [ "$(DEBUG)" != "0" ]; then \
		echo "  - Running: $(PY) -m cli.harvest pubmed $(INST) $(KEYS) $@"; \
	fi
	@$(PY) -m cli.harvest pubmed $(INST) $(KEYS) $@ 2>&1 | tee -a harvest.log
	@echo "[$(shell date +'%Y-%m-%d %H:%M:%S')] Completed PubMed data harvest"

$(EUPMC_JSONL): $(PUBMED_JSONL) $(SETT)
	@echo "[$(shell date +'%Y-%m-%d %H:%M:%S')] Starting Europe PMC data harvest..."
	@echo "  - Input files: $(PUBMED_JSONL), $(SETT)"
	@echo "  - Output file: $@"
	@if [ "$(DEBUG)" != "0" ]; then \
		echo "  - Debug mode: enabled"; \
	fi
	@mkdir -p $(BRONZE)
	@if [ "$(DEBUG)" != "0" ]; then \
		echo "  - Running: $(PY) -m cli.harvest eupmc $(PUBMED_JSONL) $@"; \
	fi
	@$(PY) -m cli.harvest eupmc $(PUBMED_JSONL) $@ 2>&1 | tee -a harvest.log
	@echo "[$(shell date +'%Y-%m-%d %H:%M:%S')] Completed Europe PMC data harvest"

silver: $(EXTRACTS_JL)
	@echo "[$(shell date +'%Y-%m-%d %H:%M:%S')] Completed silver target"

$(CORPUS_JSONL): $(PUBMED_JSONL) $(EUPMC_JSONL) $(SETT)
	@echo "[$(shell date +'%Y-%m-%d %H:%M:%S')] Starting corpus build..."
	@echo "  - Input files: $(PUBMED_JSONL), $(EUPMC_JSONL), $(SETT)"
	@echo "  - Output file: $@"
	@if [ "$(DEBUG)" != "0" ]; then \
		echo "  - Debug mode: enabled"; \
	fi
	@mkdir -p $(SILVER)
	@if [ "$(DEBUG)" != "0" ]; then \
		echo "  - Running: $(PY) -m cli.corpus $(PUBMED_JSONL) $(EUPMC_JSONL) $@"; \
	fi
	@$(PY) -m cli.corpus $(PUBMED_JSONL) $(EUPMC_JSONL) $@ 2>&1 | tee -a corpus_build.log
	@echo "[$(shell date +'%Y-%m-%d %H:%M:%S')] Completed corpus build"

# Debug target - same as make silver but with debug enabled
debug:
	@$(MAKE) silver DEBUG=1

$(EXTRACTS_JL): $(CORPUS_JSONL)
	@echo "[$(shell date +'%Y-%m-%d %H:%M:%S')] Starting LLM extraction..."
	@echo "  - Input file: $(CORPUS_JSONL)"
	@echo "  - Output file: $@"
	@echo "  - Debug mode: $(if $(filter 1,$(DEBUG)),enabled,disabled)"
	@echo "  - Python: $(shell which python)"
	@echo "  - Python version: $(shell python --version 2>&1)"
	@echo "  - PyTorch version: $(shell python -c 'import torch; print(torch.__version__)' 2>&1)"
	@echo "  - CUDA available: $(shell python -c 'import torch; print(torch.cuda.is_available())' 2>&1)"
	@echo "  - Number of CPU cores: $(shell nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 'unknown')"
	@echo "  - Available RAM: $(shell sysctl -n hw.memsize 2>/dev/null | awk '{print int($$0/1024/1024)"MB"}' || echo 'unknown')"
	@echo "  - Disk space in data/silver: $(shell du -sh data/silver 2>/dev/null || echo 'unknown')"
	@echo "  - Input file size: $(shell du -h $(CORPUS_JSONL) 2>/dev/null || echo 'unknown')"
	@echo "  - Input file line count: $(shell wc -l < $(CORPUS_JSONL) 2>/dev/null || echo 'unknown')"
	@echo ""
	@echo "[$(shell date +'%Y-%m-%d %H:%M:%S')] Running extraction command..."
	@mkdir -p $(SILVER)
	@if [ "$(DEBUG)" != "0" ]; then \
		echo "  - Running: PYTHONPATH=$(PWD)/src $(PY) -m cli.extract $(CORPUS_JSONL) $@ --batch-size 2 --debug"; \
	fi
	@./run_debug.sh
	@echo ""
	@echo "[$(shell date +'%Y-%m-%d %H:%M:%S')] LLM extraction completed"
	@echo "  - Output file size: $(shell du -h $@ 2>/dev/null || echo 'unknown')"
	@echo "  - Output file line count: $(shell wc -l < $@ 2>/dev/null || echo 'unknown')"

$(EXTRACTS_CSV): $(EXTRACTS_JL) $(LABS_CSV) $(CORPUS_JSONL)
	@echo "[$(shell date +'%Y-%m-%d %H:%M:%S')] Starting extractions consolidation..."
	@echo "  - Input files: $(EXTRACTS_JL), $(LABS_CSV), $(CORPUS_JSONL)"
	@echo "  - Output file: $@"
	@if [ "$(DEBUG)" != "0" ]; then \
		echo "  - Debug mode: enabled"; \
	fi
	@mkdir -p $(GOLD)
	@if [ "$(DEBUG)" != "0" ]; then \
		echo "  - Running: $(PY) -m cli.consolidate $(EXTRACTS_JL) $@ --corpus $(CORPUS_JSONL)"; \
	fi
	@$(PY) -m cli.consolidate $(EXTRACTS_JL) $@ --corpus $(CORPUS_JSONL) 2>&1 | tee -a consolidate.log
	@echo "[$(shell date +'%Y-%m-%d %H:%M:%S')] Completed extractions consolidation"

gold: $(EXTRACTS_CSV) $(LABS_CSV) $(LABS_GEOJSON)
	@echo "[$(shell date +'%Y-%m-%d %H:%M:%S')] Completed gold target"

# Generate labs.csv from institutions.txt
$(LABS_CSV): config/institutions.txt
	@echo "[$(shell date +'%Y-%m-%d %H:%M:%S')] Generating labs.csv from institutions.txt..."
	@mkdir -p data
	@$(PY) scripts/generate_labs_csv.py

$(LABS_GEOJSON): $(EXTRACTS_CSV) $(LABS_CSV)
	@echo "[$(shell date +'%Y-%m-%d %H:%M:%S')] Starting GeoJSON generation..."
	@echo "  - Input files: $(LABS_CSV), $(EXTRACTS_CSV)"
	@echo "  - Output file: $@"
	mkdir -p $(GOLD)
	cd $(dir $(realpath $(firstword $(MAKEFILE_LIST)))) && \
	$(PY) -m cli.geo $(LABS_CSV) $(EXTRACTS_CSV) $@
	@echo "[$(shell date +'%Y-%m-%d %H:%M:%S')] Completed GeoJSON generation"

# Install web dependencies
web-install: web-backend-install web-frontend-install

# Install backend dependencies
web-backend-install:
	@echo "[$(shell date +'%Y-%m-%d %H:%M:%S')] Installing backend dependencies..."
	@echo "[$(shell date +'%Y-%m-%d %H:%M:%S')] Installing dependencies from requirements.txt..."
	cd web/backend && $(PIP) install -r requirements.txt

# Install frontend dependencies
web-frontend-install:
	@echo "[$(shell date +'%Y-%m-%d %H:%M:%S')] Installing frontend dependencies..."
	cd web/frontend && npm install

# Build frontend
web-build:
	@echo "[$(shell date +'%Y-%m-%d %H:%M:%S')] Building frontend..."
	cd web/frontend && npm run build

# Run the development servers
web:
	@echo "[$(shell date +'%Y-%m-%d %H:%M:%S')] Cleaning up frontend dependencies..."
	rm -rf web/frontend/node_modules web/frontend/package-lock.json

	@echo "[$(shell date +'%Y-%m-%d %H:%M:%S')] Installing backend dependencies..."
	cd web/backend && $(PIP) install -r requirements.txt

	@echo "[$(shell date +'%Y-%m-%d %H:%M:%S')] Installing frontend dependencies..."
	cd web/frontend && npm install --legacy-peer-deps

	@echo "[$(shell date +'%Y-%m-%d %H:%M:%S')] Starting development servers..."
	@echo "[$(shell date +'%Y-%m-%d %H:%M:%S')] Starting backend server on http://localhost:8000"
	@echo "[$(shell date +'%Y-%m-%d %H:%M:%S')] Starting frontend server on http://localhost:3000"
	@echo ""
	@echo "Access the application at: http://localhost:3000"
	@echo "API documentation: http://localhost:8000/docs"
	@echo ""
	@echo "Press Ctrl+C to stop both servers"
	@echo ""
	@# Create a script to run both servers
	@echo '#!/bin/bash' > /tmp/run_servers.sh
	@echo 'cd "$(CURDIR)/web/backend" && $(PY) -m uvicorn app.main:app --reload --port 8000 > ../backend.log 2>&1 &' >> /tmp/run_servers.sh
	@echo 'BACKEND_PID=$$!' >> /tmp/run_servers.sh
	@echo 'echo $$BACKEND_PID > /tmp/bslmap_backend.pid' >> /tmp/run_servers.sh
	@echo 'cd "$(CURDIR)/web/frontend" && npm run dev 2>&1 | tee -a ../frontend.log' >> /tmp/run_servers.sh
	@echo 'kill $$BACKEND_PID 2>/dev/null || true' >> /tmp/run_servers.sh
	@echo 'rm -f /tmp/bslmap_backend.pid' >> /tmp/run_servers.sh
	@chmod +x /tmp/run_servers.sh
	@/tmp/run_servers.sh

# Stop development servers
web-stop:
	@if [ -f /tmp/bslmap_backend.pid ]; then \
	  echo "Stopping backend server (PID: $$(cat /tmp/bslmap_backend.pid))"; \
	  kill -9 $$(cat /tmp/bslmap_backend.pid) 2>/dev/null || true; \
	  rm -f /tmp/bslmap_backend.pid; \
	fi
	@if [ -f web/frontend.pid ]; then \
	  echo "Stopping frontend server (PID: $$(cat web/frontend.pid))"; \
	  kill $$(cat web/frontend.pid) 2>/dev/null || true; \
	  rm -f web/frontend.pid; \
	fi
	@rm -f web/*.log

# Clean web artifacts
web-clean:
	@echo "[$(shell date +'%Y-%m-%d %H:%M:%S')] Cleaning web artifacts..."
	@rm -rf web/backend/__pycache__ web/backend/*.pyc
	@rm -rf web/frontend/node_modules web/frontend/dist web/frontend/.vite
	@rm -f web/backend.pid web/frontend.pid web/*.log

# Add web-clean to the main clean target
clean: web-clean