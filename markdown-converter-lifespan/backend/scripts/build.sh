#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
test -f frontend/dist/index.html || { echo 'Build frontend/dist and include it before deployment.'; exit 1; }
python -m pip install torch==2.14.0+cpu torchvision==0.29.0+cpu --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r backend/requirements.txt
OMP_NUM_THREADS=2 TOKENIZERS_PARALLELISM=false python backend/scripts/prepare_models.py
