#!/bin/bash -e

set -x

source helpers_root/dev_scripts_helpers/thin_client/thin_client_utils.sh

# The repo that we are using as reference (can be `helpers` or a super-repo).
SRC_PREFIX="helpers"

#SRC_ROOT_DIR="/Users/saggese/src/sports_analytics1/helpers_root"
SRC_ROOT_DIR=$(pwd)"/helpers_root"
#SRC_ROOT_DIR="/Users/saggese/src/orange1"

# The new repo that we are creating / syncing.
DST_PREFIX="tutorials"
#DST_PREFIX="sports_analytics"
#DST_ROOT_DIR="/Users/saggese/src/tutorials1"
DST_ROOT_DIR=$(pwd)

#DST_PREFIX="sports_analytics"
#DST_ROOT_DIR="/Users/saggese/src/sports_analytics1"

#DST_ROOT_DIR="/Users/saggese/src/orange1/amp"

# 1) Copy / customize files in `thin_client`.
if [[ 1 == 1 ]]; then
    SRC_DIR="$SRC_ROOT_DIR/dev_scripts_${SRC_PREFIX}/thin_client"
    dassert_dir_exists $SRC_DIR
    DST_DIR="$DST_ROOT_DIR/dev_scripts_${DST_PREFIX}/thin_client"
    dassert_dir_exists $DST_DIR
    vimdiff ${SRC_DIR}/setenv.sh ${DST_DIR}/setenv.sh
    vimdiff ${SRC_DIR}/tmux.py ${DST_DIR}/tmux.py
fi;


# 2) Copy / customize files in top dir.
if [[ 1 == 1 ]]; then
    files_to_copy=(
        "changelog.txt"
        "conftest.py"
        "invoke.yaml"
        "pytest.ini"
        "repo_config.py"
        "tasks.py"
    )
    for file in "${files_to_copy[@]}"; do
        vimdiff "$SRC_ROOT_DIR/$file" $DST_ROOT_DIR
    done
fi;


# 3) Copy / customize files in devops.
if [[ 1 == 1 ]]; then
    diff_to_vimdiff.py --dir1 devops --dir2 helpers_root/devops
fi;


# 4) Compare .github/workflows
if [[ 0 == 1 ]]; then
    diff_to_vimdiff.py --dir1 .github --dir2 helpers_root/.github
fi;
