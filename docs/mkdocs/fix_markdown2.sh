#!/bin/bash -e
# Usage: ./fix_markdown.sh <file.md>
# Cleans smart quotes, weird Unicode artifacts, and replacement chars.

if [ $# -eq 0 ]; then
    echo "Usage: $0 <file.md>"
    exit 1
fi

file="$1"

if [ ! -f "$file" ]; then
    echo "Error: File '$file' not found"
    exit 1
fi

echo "Processing $file..."

# Fix common malformed sequences first.
perl -pi -e "s/’/'/g" "$file"
perl -pi -e 's/“/"/g' "$file"
perl -pi -e 's/”/"/g' "$file"

perl -ni -e 'print unless /^---\s*$/' $file

perl -i -pe 's/\n{2,}/\n\n/g' $file

lint_txt.py -i $file --use_dockerized_prettier --use_dockerized_markdown_toc --skip_action refresh_toc
