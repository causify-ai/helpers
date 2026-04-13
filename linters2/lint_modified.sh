#!/bin/bash

echo "# Files added / modified in current Git client:"
git diff --name-only --diff-filter=AM HEAD | \grep py | tee tmp

echo "# Linting"
pre-commit run --files $(cat tmp)

linters2/normalize_import.py $(cat tmp)
linters2/add_class_frames.py $(cat tmp)
