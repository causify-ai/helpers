#!/bin/bash -xe

# """
# This script preprocesses markdown files from the docs directory and serves
# them locally using mkdocs for preview during development.
#
# Usage: ./helpers_root/docs_mkdocs/render_local.sh [port]
#
# Example:
# > cd /Users/VedanshuJoshi/Downloads/csfy-master
# > helpers_root/docs_mkdocs/render_local.sh
# > helpers_root/docs_mkdocs/render_local.sh 8003
# """

PORT=${1:-8002}
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

# Copy helpers docs into the csfy docs tree (mirrors CI step).
mkdir -p docs/helpers
if [ -d "helpers_root/docs" ]; then
    cp -rL helpers_root/docs/* docs/helpers/ 2>/dev/null || true
fi

# Preprocess docs into tmp.mkdocs.
source "$HOME/src/venv/mkdocs/bin/activate"
PYTHONPATH="$REPO_ROOT:$REPO_ROOT/helpers_root" \
    python helpers_root/docs_mkdocs/preprocess_mkdocs.py \
    --input_dir docs --output_dir tmp.mkdocs -v INFO

# Serve.
cd tmp.mkdocs
mkdocs serve --dev-addr "0.0.0.0:$PORT"
