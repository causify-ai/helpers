#
# Configure the Docker container environment for development.
# It corresponds to the script `dev_scripts/setXYZ.sh` outside of the
# container.
#

set -e

# IS_SUPER_REPO=1
IS_SUPER_REPO=0
echo "IS_SUPER_REPO=$IS_SUPER_REPO"

SCRIPT_PATH="devops/docker_run/docker_setenv.sh"
echo "##> $SCRIPT_PATH"

# - Source `utils.sh`.
# NOTE: we can't use $0 to find the path since we are sourcing this file.
GIT_ROOT_DIR=$(pwd)
echo "GIT_ROOT_DIR=$GIT_ROOT_DIR"

if [[ $IS_SUPER_ROOT == 1 ]]; then
    HELPERS_ROOT="${GIT_ROOT_DIR}/helpers_root"
else
    HELPERS_ROOT=$GIT_ROOT_DIR
fi;
SOURCE_PATH="${HELPERS_ROOT}/dev_scripts_helpers/thin_client/thin_client_utils.sh"
echo "> source $SOURCE_PATH ..."
if [[ ! -f $SOURCE_PATH ]]; then
    echo -e "ERROR: Can't find $SOURCE_PATH"
    kill -INT $$
fi
source $SOURCE_PATH

# - Activate venv.
activate_docker_venv

if [[ IS_SUPER_REPO == 1 ]]; then
    HELPERS_ROOT_DIR="${GIT_ROOT_DIR}/helpers_root"
    dassert_dir_exists $HELPERS_ROOT_DIR
fi;

# - PATH
set_path .

# - PYTHONPATH
set_pythonpath

if [[ IS_SUPER_REPO == 1 ]]; then
    # Add helpers.
    dassert_dir_exists $HELPERS_ROOT_DIR
    export PYTHONPATH=$HELPERS_ROOT_DIR:$PYTHONPATH
fi;

# - Configure environment.
echo "# Configure env"
export PYTHONDONTWRITEBYTECODE=x
