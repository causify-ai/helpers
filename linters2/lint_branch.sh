#!/bin/bash

git diff --diff-filter=AM  --name-only master... | \grep py | tee tmp

pre-commit run --files $(cat tmp)

LINTERS2=$(find . -name linters2 -d)
$LINTERS2/normalize_import.py $(cat tmp)
$LINTERS2/add_class_frames.py $(cat tmp)
