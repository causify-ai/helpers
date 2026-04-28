#!/bin/bash
set -e

rm -f changes.patch formatted.py || true

# Read the coding rules and the file content
RULES=$(cat .claude/skills/coding.rules.md)
FILE_CONTENT=$(cat linters2/normalize_import.py)
PROMPT_INSTRUCTIONS=$(cat prompt.md)

# Build the system prompt
SYSTEM_PROMPT="You are a Python code formatter. $PROMPT_INSTRUCTIONS"

# Build the user prompt with the file content and rules
USER_PROMPT="Format this Python file according to these coding rules:

$RULES

File to format:
\`\`\`python
$FILE_CONTENT
\`\`\`

Output ONLY the formatted Python code in a code block, no explanations."

# Call llm and save the cost info
echo "Calling llm to format code..." >&2
llm "$USER_PROMPT" \
    -s "$SYSTEM_PROMPT" \
    -m openrouter/openai/gpt-oss-120b \
    -o provider '{"sort": "throughput"}' \
    -x \
    --usage \
    > formatted.py \
    2> cost.txt

# Create a diff/patch
if [[ 1 == 0 ]]; then

echo "=== Generating diff ==="
diff -u linters2/normalize_import.py formatted.py > changes.patch || true

# Show the diff
if [ -s changes.patch ]; then
    echo "Changes found:"
    head -50 changes.patch
    echo ""
    echo "To apply changes, run: git apply changes.patch"
else
    echo "No changes detected - file is already well-formatted"
fi

fi;

cp formatted.py linters2/normalize_import.py

# Show cost information
echo ""
echo "=== Cost information ==="
if command -v jq &> /dev/null; then
    cat cost.txt | sed 's/^[^{]*//' | jq '.cost' 2>/dev/null || cat cost.txt
else
    cat cost.txt
fi
