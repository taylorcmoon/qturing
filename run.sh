#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
source .venv/bin/activate
python -c "import cloud_automata_lab; print('cloud_automata_lab ready')"

echo "[run] Opening local web app..."
open wolfram_cloud_studio.html

echo "[run] Launching Wolfram Cloud Studio via wolframscript..."
wolframscript -activate -file wolfram_cloud_studio.wl
