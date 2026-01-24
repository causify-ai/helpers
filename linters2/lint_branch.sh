#!/bin/bash

echo "# Files added / modified in the current Git branch:"
git diff --diff-filter=AM  --name-only master... | \grep py | tee tmp

echo "# Linting"
pre-commit run --files $(cat tmp)

echo "# normalize_import.py"
linters2/normalize_import.py --no_report_command_line $(cat tmp)

echo "# add_class_frames.py"
linters2/add_class_frames.py --no_report_command_line $(cat tmp)
