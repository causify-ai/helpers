#!/bin/bash

echo "# Files added / modified in current Git client:"
git diff --name-only --diff-filter=AM HEAD | \grep py | tee tmp

echo "# Linting"
pre-commit run --files $(cat tmp)

LINTERS2=$(find . -name linters2 -d)
$LINTERS2/normalize_import.py $(cat tmp)
$LINTERS2/add_class_frames.py $(cat tmp)
