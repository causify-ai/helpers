#!/usr/bin/env bash
#
# git_sync_between_branches.sh
#
# Syncs a set of files/dirs in DST_BRANCH to match SRC_BRANCH exactly
# (handles added, modified, and deleted files).
#
# Usage:
# ./git_sync_between_branches.sh SRC_BRANCH DST_BRANCH FILE1 [FILE2 ...]
# ./git_sync_between_branches.sh --src_branch SRC --dst_branch DST --files "FILE1 FILE2"
# ./git_sync_between_branches.sh --help

set -euo pipefail

show_help() {
  cat <<EOF
Usage: $(basename "$0") SRC_BRANCH DST_BRANCH FILE1 [FILE2 ...]
   or: $(basename "$0") --src_branch SRC --dst_branch DST --files "FILE1 FILE2 ..."

Syncs a set of files/dirs in DST_BRANCH to match SRC_BRANCH exactly
(handles added, modified, and deleted files).

Positional Arguments (legacy):
  SRC_BRANCH      Source branch to sync from
  DST_BRANCH      Destination branch to sync to
  FILE1 [FILE2]   One or more files/directories to sync (space-separated)

Named Options:
  --src_branch SRC        Source branch to sync from
  --dst_branch DST        Destination branch to sync to
  --files "FILE1 FILE2"   Files/directories to sync (space-separated, quoted)
  --help                  Show this help message

Examples:
  # Positional style
  $(basename "$0") master feature-branch src/ README.md
  $(basename "$0") other-branch your-branch path/to/dir path/to/file.txt

  # Named options style
  $(basename "$0") --src_branch master --dst_branch feature-branch --files "src/ README.md"
  $(basename "$0") --src_branch other-branch --dst_branch your-branch --files "path/to/dir path/to/file.txt"

Environment Variables (legacy, for backward compatibility):
  SRC_BRANCH      Source branch (overridden by positional or named arguments)
  DST_BRANCH      Destination branch (overridden by positional or named arguments)
  FILES           Space-separated files (overridden by positional or named arguments)
EOF
}

if [ $# -eq 0 ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
  show_help
  exit 0
fi

# Parse arguments
SRC_BRANCH=""
DST_BRANCH=""
FILES=""

# Check if using named options or positional arguments
if [[ "$1" == --* ]]; then
  # Named options style
  while [ $# -gt 0 ]; do
    case "$1" in
      --src_branch)
        SRC_BRANCH="$2"
        shift 2
        ;;
      --dst_branch)
        DST_BRANCH="$2"
        shift 2
        ;;
      --files)
        FILES="$2"
        shift 2
        ;;
      *)
        echo "Error: Unknown option '$1'" >&2
        show_help >&2
        exit 1
        ;;
    esac
  done
else
  # Positional arguments style
  if [ $# -lt 3 ]; then
    echo "Error: At least 3 arguments required (SRC_BRANCH, DST_BRANCH, FILE1)" >&2
    echo "" >&2
    show_help >&2
    exit 1
  fi

  SRC_BRANCH="$1"
  DST_BRANCH="$2"
  shift 2
  FILES="$@"
fi

# Validate that all required arguments are provided
if [ -z "$SRC_BRANCH" ] || [ -z "$DST_BRANCH" ] || [ -z "$FILES" ]; then
  echo "Error: SRC_BRANCH, DST_BRANCH, and FILES are all required" >&2
  echo "" >&2
  show_help >&2
  exit 1
fi

echo "Syncing FILES=[$FILES] in '$DST_BRANCH' to match '$SRC_BRANCH'..."

# Make sure we're on the branch we want to modify
current_branch="$(git rev-parse --abbrev-ref HEAD)"
if [ "$current_branch" != "$DST_BRANCH" ]; then
  echo "Checking out $DST_BRANCH (currently on $current_branch)..."
  git checkout "$DST_BRANCH"
fi

# Diff SRC_BRANCH -> DST_BRANCH, scoped to FILES
# Status meaning (relative to going from SRC_BRANCH to DST_BRANCH):
#   A = exists in DST_BRANCH but not SRC_BRANCH -> delete it
#   D = exists in SRC_BRANCH but not DST_BRANCH -> restore it
#   M = modified -> overwrite with SRC_BRANCH version
git diff --name-status "$SRC_BRANCH" "$DST_BRANCH" -- $FILES | while read -r status file; do
  case "$status" in
    A)
      echo "Deleting (not in $SRC_BRANCH): $file"
      git rm -q "$file"
      ;;
    M|D)
      echo "Restoring/updating from $SRC_BRANCH: $file"
      git checkout "$SRC_BRANCH" -- "$file"
      ;;
    *)
      echo "Skipping unhandled status '$status' for: $file"
      ;;
  esac
done

echo ""
echo "Done. Review changes with:"
echo "  git status"
echo "  git diff --cached"
echo ""
echo "Then commit with:"
echo "  git commit -m \"Sync \$FILES with \$SRC_BRANCH\""
