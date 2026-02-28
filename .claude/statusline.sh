#!/bin/bash
# Read JSON data that Claude Code sends to stdin.
input=$(cat)

# Extract fields using jq.
MODEL=$(echo "$input" | jq -r '.model.display_name')
DIR=$(echo "$input" | jq -r '.workspace.current_dir')
# The "// 0" provides a fallback if the field is null.
PCT=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1)
COST=$(echo "$input" | jq -r '.cost.total_cost_usd // 0')
IN_TOK=$(echo "$input" | jq -r '.context_window.total_input_tokens // 0')
OUT_TOK=$(echo "$input" | jq -r '.context_window.total_output_tokens // 0')
LINES_ADDED=$(echo "$input" | jq -r '.cost.total_lines_added // 0')
LINES_REMOVED=$(echo "$input" | jq -r '.cost.total_lines_removed // 0')
VIM=$(echo "$input" | jq -r '.vim.mode // ""')

# Format cost to 4 decimal places.
COST_FMT=$(printf "%.4f" "$COST")

# ANSI color codes.
YELLOW='\033[33m'
GREEN='\033[32m'
RED='\033[31m'
RESET='\033[0m'

# Build the status line.
# - ${DIR##*/} extracts just the folder name from the full path.
# - Cost is shown first in yellow, lines added in green, lines removed in red.
STATUS="${YELLOW}\$${COST_FMT}${RESET} ${GREEN}+${LINES_ADDED}${RESET} ${RED}-${LINES_REMOVED}${RESET} | [${MODEL}] ${DIR##*/} | in:${IN_TOK} out:${OUT_TOK} | ${PCT}% ctx"

# Append vim mode only when it is non-empty.
if [ -n "$VIM" ]; then
    STATUS="${STATUS} | ${VIM}"
fi

printf "%b\n" "$STATUS"
