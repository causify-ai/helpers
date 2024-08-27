#
# Configure the local (thin) client built with `thin_client.../build.py`.
#
# NOTE: This file needs to be sourced and not executed. For this reason doesn't
# use bash and doesn't have +x permissions.
# 

DIR_TAG="helpers"

# NOTE: We can't use $0 to find out in which file we are in, since this file is
# sourced and not executed.
# TODO(gp): For symmetry consider calling the dir `dev_scripts_${DIR_TAG}`.
SCRIPT_PATH="dev_scripts/thin_client/setenv.${DIR_TAG}.sh"
echo "##> $SCRIPT_PATH"

VENV_TAG="helpers"

# Give permissions to read / write to user and group.
umask 002

# Source `utils.sh`.
# NOTE: we can't use $0 to find the path since we are sourcing this file.
GIT_ROOT_DIR=$(pwd)
echo "GIT_ROOT_DIR=$GIT_ROOT_DIR"

SOURCE_PATH="${GIT_ROOT_DIR}/dev_scripts/thin_client/thin_client_utils.sh"
echo "> source $SOURCE_PATH ..."
if [[ ! -f $SOURCE_PATH ]]; then
    echo -e "ERROR: Can't find $SOURCE_PATH"
    kill -INT $$
fi
source $SOURCE_PATH

activate_venv $VENV_TAG

# PATH
DEV_SCRIPT_DIR="${GIT_ROOT_DIR}/dev_scripts"
echo "DEV_SCRIPT_DIR=$DEV_SCRIPT_DIR"
dassert_dir_exists $DEV_SCRIPT_DIR

# Set basic vars.
set_path $DEV_SCRIPT_DIR

# PYTHONPATH
set_pythonpath

configure_specific_project

print_env_signature

echo -e "${INFO}: ${SCRIPT_PATH} successful"
