#!/bin/bash

echo "# Files added / modified in the current Git branch:"
git diff --diff-filter=AM  --name-only master... | \grep py | tee tmp

echo "# Linting"
pre-commit run --files $(cat tmp)

linters2/normalize_import.py $(cat tmp)
linters2/add_class_frames.py $(cat tmp)
