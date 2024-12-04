#
# Configure the Docker container environment for development.
# It corresponds to the script `dev_scripts/setXYZ.sh` outside of the
# container.
#

set -e

echo "CK_IS_SUPER_REPO=$CK_IS_SUPER_REPO"

SCRIPT_PATH="devops/docker_run/docker_setenv.sh"
echo "##> $SCRIPT_PATH"

# - Source `utils.sh`.
# NOTE: we can't use $0 to find the path since we are sourcing this file.

SOURCE_PATH="${CK_HELPERS_ROOT_PATH}/dev_scripts_helpers/thin_client/thin_client_utils.sh"
echo "> source $SOURCE_PATH ..."
if [[ ! -f $SOURCE_PATH ]]; then
    echo -e "ERROR: Can't find $SOURCE_PATH"
    kill -INT $$
fi
source $SOURCE_PATH

# - Activate venv.
activate_docker_venv

if [[ $CK_IS_SUPER_REPO == 1 ]]; then
    dassert_dir_exists $CK_HELPERS_ROOT_PATH
fi;

# - PATH
set_path .

# - PYTHONPATH
set_pythonpath

if [[ $CK_IS_SUPER_REPO == 1 ]]; then
    # Add helpers.
    dassert_dir_exists $CK_HELPERS_ROOT_PATH
    export PYTHONPATH=$CK_HELPERS_ROOT_PATH:$PYTHONPATH
fi;

# - Configure environment.
echo "# Configure env"
export PYTHONDONTWRITEBYTECODE=x
