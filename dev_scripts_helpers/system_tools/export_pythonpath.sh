#!/bin/bash
# Usage: source set_pythonpath.sh /path/to/start

START_DIR="${1:-$(pwd)}"
# Clear PYTHONPATH.
export PYTHONPATH=""
PYTHONPATH="$(realpath $START_DIR)"
# Move into root to properly resolve submodules.
cd "$START_DIR" || { echo "❌ Failed to change directory to $START_DIR"; exit 1; }
# Add all submodule paths (recursively).
SUBMODULES_PATHS=$(git submodule foreach --quiet --recursive 'echo $(pwd)' | paste -sd:)
PYTHONPATH="$PYTHONPATH:$SUBMODULES_PATHS"
# Export and show final PYTHONPATH.
export PYTHONPATH
echo "PYTHONPATH=$PYTHONPATH"
