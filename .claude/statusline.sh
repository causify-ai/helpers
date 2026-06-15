#!/bin/bash
# Status line for Claude Code.
#
# Reads JSON input from Claude Code (via stdin) and renders a compact status
# bar showing cost, diff lines, model, directory, tokens, and context usage.
#
# Cost is computed by helpers_root/.claude/compute_cost.py using the CC_MODEL
# env var (set by helpers_root/dev_scripts_helpers/ai/cc).

input=$(cat)

# Extract fields.
MODEL=$(echo "$input" | jq -r '.model.display_name')
MODEL_ID=$(echo "$input" | jq -r '.model.api_model // ""')
DIR=$(echo "$input" | jq -r '.workspace.current_dir')
# The "// 0" provides a fallback if the field is null.
PCT=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1)
REPORTED_COST=$(echo "$input" | jq -r '.cost.total_cost_usd // 0')
IN_TOK=$(echo "$input" | jq -r '.context_window.total_input_tokens // 0')
OUT_TOK=$(echo "$input" | jq -r '.context_window.total_output_tokens // 0')
LINES_ADDED=$(echo "$input" | jq -r '.cost.total_lines_added // 0')
LINES_REMOVED=$(echo "$input" | jq -r '.cost.total_lines_removed // 0')
VIM=$(echo "$input" | jq -r '.vim.mode // ""')

# Colors.
YELLOW='\033[33m'
GREEN='\033[32m'
RED='\033[31m'
CYAN='\033[36m'
RESET='\033[0m'

# Compute cost from tokens.
# Delegate to Python script which has the pricing table and CC_MODEL lookup.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COST_FMT=$(python3 "$SCRIPT_DIR/compute_cost.py" \
    "$MODEL" "$MODEL_ID" "$IN_TOK" "$OUT_TOK" "$REPORTED_COST" 2>/dev/null)

# Fallback if python3 call failed or returned empty.
if [ -z "$COST_FMT" ]; then
    COST_FMT=$(printf "%.4f" "$REPORTED_COST")
fi

# Build status line.
MODEL_TAG="${SHORT_LABEL}${CC_FLAG:+ ${CC_FLAG}}"

STATUS="${YELLOW}\$${COST_FMT}${RESET} ${GREEN}+${LINES_ADDED}${RESET} ${RED}-${LINES_REMOVED}${RESET} | [${MODEL_TAG}] ${DIR##*/} | in:${IN_TOK} out:${OUT_TOK} | ${PCT}% ctx"

# Append vim mode only when it is non-empty.
if [ -n "$VIM" ]; then
    STATUS="${STATUS} | ${VIM}"
fi

printf "%b\n" "$STATUS"
