#!/usr/bin/env bash

show_help() {
  cat << EOF
Usage: cc_usage.sh [OPTION]

Print Claude Code token usage information.

Options:
  --today       Print usage for today (default)
  --yesterday   Print usage for yesterday
  --weekly      Print usage for the last 7 days
  --help        Show this help message

Examples:
  ./cc_usage.sh              # Show today's usage
  ./cc_usage.sh --yesterday  # Show yesterday's usage
  ./cc_usage.sh --weekly     # Show last 7 days' usage
EOF
}

# Default to today
period="today"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --yesterday)
      period="yesterday"
      shift
      ;;
    --weekly)
      period="weekly"
      shift
      ;;
    --help)
      show_help
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      show_help
      exit 1
      ;;
  esac
done

# Helper to subtract days (works on both macOS and Linux)
subtract_days() {
  local days=$1
  if date -d "1 day ago" &>/dev/null; then
    # GNU date (Linux)
    date -d "$days days ago" +%Y-%m-%d
  else
    # BSD date (macOS)
    date -v-"${days}d" +%Y-%m-%d
  fi
}

# Execute based on period
case $period in
  today)
    ccusage claude daily --breakdown --since $(date +%Y-%m-%d) --compact --no-color
    ;;
  yesterday)
    yesterday=$(subtract_days 1)
    ccusage claude daily --breakdown --since "$yesterday" --until "$yesterday" --compact --no-color
    ;;
  weekly)
    week_ago=$(subtract_days 7)
    ccusage claude daily --breakdown --since "$week_ago" --compact --no-color
    ;;
esac
