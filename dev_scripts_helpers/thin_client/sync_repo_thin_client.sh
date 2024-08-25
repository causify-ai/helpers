#!/bin/bash -x

#set -e

# The repo that we are using as reference (can be `helpers` or a super-repo).
SRC_PREFIX="helpers"
SRC_ROOT_DIR="/Users/saggese/src/sports_analytics1/helpers_root"
#SRC_ROOT_DIR="/Users/saggese/src/orange1"

# The new repo that we are creating / syncing.
#DST_PREFIX="tutorials"
#DST_ROOT_DIR="/Users/saggese/src/tutorials1"
#DST_ROOT_DIR="/Users/saggese/src/orange1/amp"
DST_PREFIX="sports_analytics"
DST_ROOT_DIR="/Users/saggese/src/sports_analytics1"


if [[ 1 == 1 ]]; then
    SRC_DIR="$SRC_ROOT_DIR/dev_scripts_${SRC_PREFIX}/thin_client"
    DST_DIR="$DST_ROOT_DIR/dev_scripts_${DST_PREFIX}/thin_client"
    # Template vs dst dir.
    vimdiff ${SRC_DIR}/setenv.sh ${DST_DIR}/setenv.sh
    vimdiff ${SRC_DIR}/tmux.py ${DST_DIR}/tmux.py
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
