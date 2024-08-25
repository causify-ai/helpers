#!/bin/bash -x

#set -e

# The repo that we are using as reference (can be `helpers` or a super-repo).
SRC_ROOT_DIR="/Users/saggese/src/sports_analytics1/helpers_root"
#SRC_ROOT_DIR="/Users/saggese/src/orange1"

# The new repo that we are creating / syncing.
PREFIX="tutorials"
DST_ROOT_DIR="/Users/saggese/src/tutorials1"
#DST_ROOT_DIR="/Users/saggese/src/orange1/amp"


if [[ 1 == 1 ]]; then
    TEMPLATE_DIR="$SRC_ROOT_DIR/dev_scripts/thin_client/templates"
    DST_DIR="$DST_ROOT_DIR/dev_scripts_${PREFIX}/thin_client"
    # Template vs helpers.
    vimdiff ${TEMPLATE_DIR}/setenv.template.sh dev_scripts/thin_client/setenv.helpers.sh
    vimdiff ${TEMPLATE_DIR}/tmux.template.py dev_scripts/thin_client/tmux.helpers.py

    # Template vs dst dir.
    vimdiff ${TEMPLATE_DIR}/setenv.template.sh ${DST_DIR}/setenv.${PREFIX}.sh
    vimdiff ${TEMPLATE_DIR}/tmux.template.py ${DST_DIR}/tmux.${PREFIX}.py
fi;


if [[ 1 == 0 ]]; then
    DST_DIR="$DST_ROOT_DIR"
    files_to_copy=(
        "changelog.txt"
        "conftest.py"
        "invoke.yaml"
        "pytest.ini"
        "repo_config.py"
        "tasks.py"
    )
    for file in "${files_to_copy[@]}"; do
        vimdiff "$SRC_ROOT_DIR/$file" $DST_DIR
    done
fi;
