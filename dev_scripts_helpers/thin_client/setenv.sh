#
# Configure the local (thin) client built with `thin_client.../build.py`.
#
# NOTE: This file needs to be sourced and not executed. For this reason doesn't
# use bash and doesn't have +x permissions.
# 

DIR_TAG="helpers"

# NOTE: We can't use $0 to find out in which file we are in, since this file is
# sourced and not executed.
SCRIPT_PATH="dev_scripts_${DIR_TAG}/thin_client/setenv.sh"
echo "##> $SCRIPT_PATH"

# To customize: xyz
# IS_SUPER_REPO=1
IS_SUPER_REPO=0
echo "IS_SUPER_REPO=$IS_SUPER_REPO"

if [[ $IS_SUPER_REPO == 1 ]]; then
    # We can reuse the thin environment of `helpers` or create a new one.
    VENV_TAG="xyz"
else
    VENV_TAG="helpers"
fi;

# Give permissions to read / write to user and group.
umask 002

# - Source `utils.sh`.
# NOTE: we can't use $0 to find the path since we are sourcing this file.
GIT_ROOT_DIR=$(git rev-parse --show-toplevel)
echo "GIT_ROOT_DIR=$GIT_ROOT_DIR"

if [[ $IS_SUPER_REPO == 1 ]]; then
    # For super-repos `GIT_ROOT_DIR` points to the super-repo.
    HELPERS_ROOT_DIR="${GIT_ROOT_DIR}/helpers_root"
else
    HELPERS_ROOT_DIR="${GIT_ROOT_DIR}"
fi;
SOURCE_PATH="${HELPERS_ROOT_DIR}/dev_scripts_helpers/thin_client/thin_client_utils.sh"
echo "> source $SOURCE_PATH ..."
if [[ ! -f $SOURCE_PATH ]]; then
    echo -e "ERROR: Can't find $SOURCE_PATH"
    kill -INT $$
fi
source $SOURCE_PATH

# - Activate environment
activate_venv $VENV_TAG

if [[ $IS_SUPER_REPO == 1 ]]; then
    HELPERS_ROOT_DIR="${GIT_ROOT_DIR}/helpers_root"
    echo "HELPERS_ROOT_DIR=$HELPERS_ROOT_DIR"
    dassert_dir_exists $HELPERS_ROOT_DIR
fi;

# - PATH

# Set vars for this dir.
DEV_SCRIPT_DIR="${GIT_ROOT_DIR}/dev_scripts_${DIR_TAG}"
echo "DEV_SCRIPT_DIR=$DEV_SCRIPT_DIR"
dassert_dir_exists $DEV_SCRIPT_DIR

# Set basic vars.
set_path $DEV_SCRIPT_DIR

if [[ $IS_SUPER_REPO == 1 ]]; then
    # Set vars for helpers_root.
    set_path "${HELPERS_ROOT_DIR}/dev_scripts_helpers"
fi;

# - PYTHONPATH
set_pythonpath

if [[ $IS_SUPER_REPO == 1 ]]; then
    # Add helpers.
    dassert_dir_exists $HELPERS_ROOT_DIR
    export PYTHONPATH=$HELPERS_ROOT_DIR:$PYTHONPATH

    # We need to give priority to the local `repo_config` over the one in
    # `helpers_root`.
    export PYTHONPATH=$(pwd):$PYTHONPATH

    # Remove duplicates.
    export PYTHONPATH=$(remove_dups $PYTHONPATH)

    # Print.
    echo "PYTHONPATH=$PYTHONPATH"
fi;

# - Set specific configuration of the project.
configure_specific_project

print_env_signature

echo -e "${INFO}: ${SCRIPT_PATH} successful"
