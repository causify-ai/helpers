#!/bin/bash -e
FILES=$(find docs -name "*.md" | sort)

for FILE in $FILES; do
    echo $FILE
    lint_text.py -i $FILE
done
