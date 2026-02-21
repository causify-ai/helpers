#!/bin/bash

echo "# Files added / modified in the current Git branch:"
{
  git diff --diff-filter=AM --name-only master...
  git diff --name-only --diff-filter=AM HEAD
} | grep -E '\.(py|ipynb)$' | sort -u > tmp

echo "# Linting"
pre-commit run --files $(cat tmp) | tee precommit.log.txt

echo "# normalize_import.py"
linters2/normalize_import.py --no_report_command_line $(cat tmp)

echo "# add_class_frames.py"
linters2/add_class_frames.py --no_report_command_line $(cat tmp)

# ls -1 docs/ai_prompts/*.md | xargs -n 1 lint_txt.py -i

# uvx vulture . | grep -v ipynb_checkpoints
