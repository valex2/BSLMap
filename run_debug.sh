#!/bin/bash
set -e

# Activate conda environment and run extraction with debug
source $(conda info --base)/etc/profile.d/conda.sh
conda activate bslmap

# Set environment variables
export PYTHONUNBUFFERED=1
export PYTHONIOENCODING=UTF-8
export PYTHONPATH=/Users/Vassilis/Desktop/BSLMap/src
export DEBUG=1

# Run the extraction with optimized batch size
python -m cli.extract data/silver/corpus.jsonl data/silver/extractions.jsonl --batch-size 8 --debug 2>&1 | tee -a extract.log
