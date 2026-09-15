#!/usr/bin/env bash
# PreToolUse hook: remind Claude to follow the right `.claude/rules.md` rules
# before it writes or edits a file, based on the file's path/extension.
#
# `.claude/rules.md` maps "file type" -> rules/template files, but that
# dispatch table is a manual lookup (nothing forces Claude to re-read it before
# every edit). This hook automates the part of the mapping that is derivable
# purely from `file_path` (extension or path convention): coding, bash,
# testing, notebooks, typst. Rules keyed on document *purpose* rather than path
# (e.g., blog posts, READMEs, structured bullet text, slides) are NOT covered
# here: a file path alone cannot tell a blog post from a plain markdown doc, so
# those stay a manual read.
#
# This hook only informs; it never blocks the edit (no `permissionDecision` is
# emitted).
#
# `RULES` is ordered most-specific-first; the first regex that matches
# `file_path` wins (e.g., `test/test_*.py` is checked before the generic
# `*.py` rule, `__init__.py` before the generic `*.py` rule).
set -euo pipefail

input_json="$(cat)"
file_path="$(printf '%s' "$input_json" | jq -r '.tool_input.file_path // empty' 2>/dev/null || true)"
[ -z "$file_path" ] && exit 0

# Each row: "<regex on file_path>|||<context message>".
RULES=(
    '(^|/)test/test_[^/]+\.py$|||This file is a unit test (matches `test/test_<file>.py`). Before proceeding, read and follow `.claude/skills/coding.rules.md` and `.claude/skills/testing.rules.md`, per `.claude/rules.md` > "Testing".'
    '(^|/)__init__\.py$|||This is a package `__init__.py`. Before proceeding, read and follow `.claude/skills/coding.rules.md` and the template `.claude/templates/__init__.py`, per `.claude/rules.md` > "Coding".'
    '\.py$|||This is a Python file. Before proceeding, read and follow `.claude/skills/coding.rules.md` and the template `.claude/templates/coding.template.py`, per `.claude/rules.md` > "Coding".'
    '\.sh$|||This is a shell script. Before proceeding, read and follow `.claude/skills/bash.rules.md`, per `.claude/rules.md` > "Bash".'
    '\.ipynb$|||This is a Jupyter notebook. Before proceeding, read and follow `.claude/skills/notebook.rules.md` and the templates `.claude/templates/notebook.template.ipynb` / `.claude/templates/notebook.template.py`, per `.claude/rules.md` > "Notebooks".'
    '\.typ$|||This is a Typst file. Before proceeding, read and follow `.claude/skills/typst.rules.md` and the template `.claude/templates/typst.template.typ`, per `.claude/rules.md` > "Typst".'
)

for row in "${RULES[@]}"; do
    regex="${row%%|||*}"
    context="${row#*|||}"
    if printf '%s' "$file_path" | grep -qE "$regex"; then
        jq -n --arg context "$context" '{
            systemMessage: "check_file_rules.sh: file-type rules reminder injected",
            hookSpecificOutput: {
                hookEventName: "PreToolUse",
                additionalContext: $context
            }
        }'
        exit 0
    fi
done
