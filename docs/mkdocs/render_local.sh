#!/bin/bash -xe
#export SRC_DIR=blog/docs/posts
export SRC_DIR=$1
export DST_DIR=tmp.mkdocs
./helpers_root/docs/mkdocs/preprocess_mkdocs.py --input $SRC_DIR --output_dir $DST_DIR

source mkdocs.venv/bin/activate

(cd dev_scripts_helpers/documentation/mkdocs; mkdocs serve --dev-addr localhost:8001 -o)
