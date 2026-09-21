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
if [[ ! -f "$NOTEBOOK" ]]; then
    echo "Error: notebook '$NOTEBOOK' not found"
    exit 1
fi

# `docker_cmd.sh` and `docker_name.sh` live in the dir of the notebook (each
# tutorial dir has its own Docker setup), not in this script dir.
NOTEBOOK_DIR=$(cd "$(dirname "$NOTEBOOK")" && pwd -P)
NOTEBOOK_NAME=$(basename "$NOTEBOOK")
DOCKER_CMD_SH="$NOTEBOOK_DIR/docker_cmd.sh"
if [[ ! -e "$DOCKER_CMD_SH" ]]; then
    echo "Error: can't find '$DOCKER_CMD_SH'"
    exit 1
fi

# Get the git root of the notebook, used to compute where the notebook dir and
# the shared template dir land inside the container (git root is mounted at
# /git_root).
GIT_ROOT=$(cd "$NOTEBOOK_DIR" && git rev-parse --show-toplevel)
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
RELPATH_PY="import os,sys; print(os.path.relpath(sys.argv[1], sys.argv[2]))"
REL_NOTEBOOK_DIR=$(python3 -c "$RELPATH_PY" "$NOTEBOOK_DIR" "$GIT_ROOT")
REL_TEMPLATE_DIR=$(python3 -c "$RELPATH_PY" \
    "$SCRIPT_DIR/nbconvert_templates" "$GIT_ROOT")

# Build the nbconvert command to run inside the container. `cd` into the
# matching /git_root path first: docker_cmd.sh does not start the container
# in this dir, so a relative notebook path would otherwise match no files.
CMD="cd /git_root/$REL_NOTEBOOK_DIR && jupyter nbconvert --execute --to html \
--ExecutePreprocessor.timeout=-1 \
--template html_anchorfix \
--TemplateExporter.extra_template_basedirs=/git_root/$REL_TEMPLATE_DIR \
$NOTEBOOK_NAME"

# Run the command inside the Docker container via the notebook's
# `docker_cmd.sh`. Run it from the notebook dir so that it finds the right git
# root and `docker_name.sh`.
cd "$NOTEBOOK_DIR"
bash "$DOCKER_CMD_SH" "$CMD"
