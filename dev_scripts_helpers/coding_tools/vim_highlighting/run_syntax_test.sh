#!/bin/bash
# Test runner for txt_syntax highlighting

set -e

cd "$(dirname "$0")"

echo "Running txt_syntax highlighting tests..."
echo ""

# Run vim to extract syntax information (using minimal vimrc to avoid plugin issues)
vim -u test_minimal.vimrc -c 'ExportSyntax' -c 'qa!' test_syntax_examples.txt 2>/dev/null || true

if [ ! -f test_syntax_output.txt ]; then
    echo "ERROR: Failed to generate test_syntax_output.txt"
    exit 1
fi

echo "Generated test_syntax_output.txt"
echo ""
echo "=== ACTUAL OUTPUT ==="
cat test_syntax_output.txt
echo ""
echo "=== EXPECTED OUTPUT ==="
cat test_syntax_expected.txt
echo ""

# Simple comparison
echo "=== COMPARISON ==="
if diff -u test_syntax_expected.txt test_syntax_output.txt 2>/dev/null; then
    echo "✓ All tests passed!"
    exit 0
else
    echo "✗ Tests failed - see differences above"
    echo ""
    echo "To debug, open the test file in vim:"
    echo "  vim -u test_minimal.vimrc test_syntax_examples.txt"
    echo ""
    echo "Then in vim, run :ExportSyntax to regenerate output"
    exit 1
fi
# vimdiff test_syntax_expected.txt test_syntax_output.txt
