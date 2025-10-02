#!/bin/bash -xe
./dev_scripts_helpers/documentation/mkdocs/preprocess_mkdocs.py --input_dir docs --output_dir dev_scripts_helpers/documentation/mkdocs/tmp.mkdocs

source mkdocs.venv/bin/activate

(cd dev_scripts_helpers/documentation/mkdocs; mkdocs serve --dev-addr localhost:8001 -o)
