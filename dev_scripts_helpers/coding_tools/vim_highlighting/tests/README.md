# Python Unit Tests for txt_syntax Highlighting

This directory contains Python unit tests for the `txt_syntax.vim` highlighting rules.

## Overview

The tests verify that Vim's syntax highlighting correctly identifies and highlights various text patterns including:
- Math expressions (`$$...$$` and `$...$`)
- Bullet points (`*`)
- Comments (`//`)
- Images (`![](...)`)
- Code fences (``` ... ```)
- Italic and bold formatting

## Running Tests

### Run All Tests

```bash
pytest tests/test_txt_syntax.py -v
```

### Run Specific Test

```bash
pytest tests/test_txt_syntax.py::TestTxtSyntaxHighlighting::test1 -v
pytest tests/test_txt_syntax.py::TestTxtSyntaxHighlighting::test2 -v
```

### Update Golden Files

When you modify the `txt_syntax.vim` file and need to update the expected output:

```bash
pytest tests/test_txt_syntax.py --update_outcomes -v
```

This will update the golden files in `outcomes/TestTxtSyntaxHighlighting.*/output/txt_syntax_output.txt`.

## Test Structure

### test1: Syntax Export Validation
- Verifies that Vim successfully exports syntax highlighting information
- Checks that the output contains expected syntax groups (e.g., `txtHeader1`, `txtHeader2`)

### test2: Syntax Output Comparison (Golden File Testing)
- Compares the actual Vim syntax output against a golden reference file
- Uses `hunitest.TestCase.check_string()` for flexible comparison
- Automatically manages golden files with `--update_outcomes`

## Golden Files

Expected outputs are stored in:
```
outcomes/TestTxtSyntaxHighlighting.test2/output/txt_syntax_output.txt
```

These files:
- Are automatically compared with actual test output
- Can be updated with `--update_outcomes` flag
- Follow the hunitest framework conventions

## Coexistence with Bash Script

The Python tests coexist with the original bash script (`run_syntax_test.sh`):
- **Bash script**: `./run_syntax_test.sh` - Quick manual testing and CI/CD
- **Python tests**: `pytest tests/test_txt_syntax.py` - Integrated with project test suite

Both can be used simultaneously without conflicts.

## Integration with Project Testing

The Python tests follow the project conventions:
- Inherit from `hunitest.TestCase`
- Use golden file testing framework
- Compatible with `--update_outcomes` flag
- Can be run as part of the standard test suite

```bash
# From helpers_root directory
pytest dev_scripts_helpers/coding_tools/vim_highlighting/tests/ -v
```
