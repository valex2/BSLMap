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
LABS_GEOJSON = $(GOLD)/labs.geojson

.PHONY: help env install lint type test clean bronze silver gold web

help:
	@echo "make env        # create/update conda env ($(CONDA_ENV))"
	@echo "make install    # install package in editable mode"
	@echo "make bronze     # PubMed/EuPMC pulls -> bronze (DEBUG=1 for verbose)"
	@echo "make silver     # corpus build -> silver (DEBUG=1 for verbose)"
	@echo "make gold       # consolidate + geojson -> gold (DEBUG=1 for verbose)"
	@echo "make debug      # run silver step with debug output (same as make silver DEBUG=1)"
	@echo "make web        # serve web/"
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

$(EXTRACTS_CSV): $(EXTRACTS_JL)
	@echo "[$(shell date +'%Y-%m-%d %H:%M:%S')] Starting extractions consolidation..."
	@echo "  - Input file: $(EXTRACTS_JL)"
	@echo "  - Output file: $@"
	@if [ "$(DEBUG)" != "0" ]; then \
		echo "  - Debug mode: enabled"; \
	fi
	@mkdir -p $(GOLD)
	@if [ "$(DEBUG)" != "0" ]; then \
		echo "  - Running: $(PY) -m cli.consolidate merge $(EXTRACTS_JL) $@"; \
	fi
	@$(PY) -m cli.consolidate merge $(EXTRACTS_JL) $@ 2>&1 | tee -a consolidate.log
	@echo "[$(shell date +'%Y-%m-%d %H:%M:%S')] Completed extractions consolidation"

gold: $(EXTRACTS_CSV) $(LABS_GEOJSON)
	@echo "[$(shell date +'%Y-%m-%d %H:%M:%S')] Completed gold target"

$(LABS_GEOJSON): $(EXTRACTS_CSV) data/labs.csv
	@echo "[$(shell date +'%Y-%m-%d %H:%M:%S')] Starting GeoJSON generation..."
	@echo "  - Input files: data/labs.csv, $(EXTRACTS_CSV)"
	@echo "  - Output file: $@"
	mkdir -p $(GOLD)
	$(PY) -m cli.geo build data/labs.csv $(EXTRACTS_CSV) $@
	@echo "[$(shell date +'%Y-%m-%d %H:%M:%S')] Completed GeoJSON generation"

web:
	$(PY) -m http.server -d web 8010