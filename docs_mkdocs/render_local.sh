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

# Preprocess docs into tmp.mkdocs.
# --collect_from_repo discovers all near-code docs/ directories in the repo
# tree and merges them into the staging area automatically.
source "$HOME/src/venv/mkdocs/bin/activate"
PYTHONPATH="$REPO_ROOT:$REPO_ROOT/helpers_root" \
    python helpers_root/docs_mkdocs/preprocess_mkdocs.py \
    --input_dir docs --output_dir tmp.mkdocs \
    --collect_from_repo "$REPO_ROOT" \
    --mkdocs_dir docs_mkdocs \
    -v INFO

# Serve.
cd tmp.mkdocs
properdocs serve --dev-addr "localhost:$PORT"
