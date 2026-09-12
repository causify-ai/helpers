#!/bin/bash
# """
# Execute a notebook top to bottom and convert it to HTML inside the Docker
# container, using the `html_anchorfix` template so that section anchors
# work in the output.
#
# `--execute` re-runs every cell instead of reusing the outputs already
# saved in the `.ipynb` file, so this is what actually verifies the
# notebook still runs end-to-end.
# """

# Exit immediately if any command exits with a non-zero status.
set -e

# Require the notebook file as the only argument.
if [[ -z "$1" ]]; then
    echo "Error: need to specify a .ipynb file"
    exit 1
fi
NOTEBOOK="$1"

# Get the git root, used to point nbconvert at the shared template dir and
# to compute where this dir lands inside the container (mounted at
# /git_root).
GIT_ROOT=$(git rev-parse --show-toplevel)
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REL_DIR=$(python3 -c "import os,sys; print(os.path.relpath(sys.argv[1], sys.argv[2]))" "$SCRIPT_DIR" "$GIT_ROOT")

# Build the nbconvert command to run inside the container. `cd` into the
# matching /git_root path first: docker_cmd.sh does not start the container
# in this dir, so a relative notebook path would otherwise match no files.
CMD="cd /git_root/$REL_DIR && jupyter nbconvert --execute --to html \
--ExecutePreprocessor.timeout=-1 \
--template html_anchorfix \
--TemplateExporter.extra_template_basedirs=/git_root/helpers_root/dev_scripts_helpers/notebooks/nbconvert_templates \
$NOTEBOOK"

# Run the command inside the Docker container via docker_cmd.sh.
$SCRIPT_DIR/docker_cmd.sh "$CMD"
