#!/bin/bash -e

(
git ls-files -m | grep -E '\.(md|txt)$' || true
git submodule foreach --quiet '
git ls-files -m | grep -E "\.(md|txt)$" | sed "s|^|$sm_path/|"
'
) | sort -u > tmp.lint_modified_md.txt

echo "# Files to line"
cat tmp.lint_modified_md.txt

cat tmp.lint_modified_md.txt | xargs -n 1 lint_txt.py -i
