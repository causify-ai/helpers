#!/bin/bash -xe

# """
# This script preprocesses markdown files from a source directory and serves
# them locally using mkdocs for preview during development.
#
# Usage: ./render_local.sh <source_directory>
#
# Example:
# > cd //csfy
# > helpers_root/docs/mkdocs/render_local.sh blog/docs/posts
# """

# Validate that a directory argument was provided.
if [ -z "$1" ]; then
  echo "Error: No directory provided"
  echo "Usage: $0 <source_directory>"
  exit 1
fi

# Assert that the provided path is a valid directory.
if [ ! -d "$1" ]; then
  echo "Error: '$1' is not a valid directory"
  exit 1
fi

#export SRC_DIR=blog/docs/posts
export SRC_DIR=$1
export DST_DIR=tmp.mkdocs
./helpers_root/docs/mkdocs/preprocess_mkdocs.py --input $SRC_DIR --output_dir $DST_DIR

#source mkdocs.venv/bin/activate

(cd dev_scripts_helpers/documentation/mkdocs; uvx mkdocs serve --dev-addr localhost:8001 -o)
