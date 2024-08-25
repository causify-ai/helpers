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
SCRIPT_PATH="dev_scripts_${DIR_TAG}/thin_client/setenv.sh"
echo "##> $SCRIPT_PATH"

# IS_SUPER_REPO=1
IS_SUPER_REPO=0
echo "IS_SUPER_REPO=$IS_SUPER_REPO"

# We can reuse the thin environment of `helpers` or create a new one.
if [[ $IS_SUPER_REPO == 1 ]]; then
    VENV_TAG="xyz"
else
    VENV_TAG="helpers"
fi;

# Give permissions to read / write to user and group.
umask 002

# Source `utils.sh`.
# NOTE: we can't use $0 to find the path since we are sourcing this file.
GIT_ROOT_DIR=$(pwd)
echo "GIT_ROOT_DIR=$GIT_ROOT_DIR"

if [[ $IS_SUPER_REPO == 1 ]]; then
    # For super-repos `GIT_ROOT_DIR` points to the super-repo.
    HELPERS_ROOT_DIR="${GIT_ROOT_DIR}/helpers_root"
else
    HELPERS_ROOT_DIR="${GIT_ROOT_DIR}"
fi;
SOURCE_PATH="${HELPERS_ROOT_DIR}/dev_scripts_${DIR_TAG}/thin_client/thin_client_utils.sh"
echo "> source $SOURCE_PATH ..."
if [[ ! -f $SOURCE_PATH ]]; then
    echo -e "ERROR: Can't find $SOURCE_PATH"
    kill -INT $$
fi
source $SOURCE_PATH

activate_venv $VENV_TAG

# PATH
DEV_SCRIPT_DIR="${GIT_ROOT_DIR}/dev_scripts_${DIR_TAG}"
echo "DEV_SCRIPT_DIR=$DEV_SCRIPT_DIR"
dassert_dir_exists $DEV_SCRIPT_DIR

# Set basic vars.
set_path $DEV_SCRIPT_DIR

if [[ $IS_SUPER_REPO == 1 ]]; then
    # Add more vars specific of the super-repo.
    export PATH=.:$PATH
    export PATH=$GIT_ROOT_DIR:$PATH
    # Add to the PATH all the first level directory under `dev_scripts`.
    export PATH="$(find $DEV_SCRIPT_DIR -maxdepth 1 -type d -not -path "$(pwd)" | tr '\n' ':' | sed 's/:$//'):$PATH"
    # Remove duplicates.
    export PATH=$(remove_dups $PATH)
    # Print.
    echo "PATH=$PATH"
fi;

# PYTHONPATH
set_pythonpath

if [[ $IS_SUPER_REPO == 1 ]]; then
    # Add more vars specific of the super-repo.
    export PYTHONPATH=$PWD:$PYTHONPATH
    # Add helpers.
    HELPERS_ROOT_DIR="$GIT_ROOT_DIR/helpers_root"
    echo "HELPERS_ROOT_DIR=$HELPERS_ROOT_DIR"
    dassert_dir_exists $HELPERS_ROOT_DIR
    export PYTHONPATH=$HELPERS_ROOT_DIR:$PYTHONPATH
    # Remove duplicates.
    export PYTHONPATH=$(remove_dups $PYTHONPATH)
    # Print.
    echo "PYTHONPATH=$PYTHONPATH"
fi;

configure_specific_project

print_env_signature

echo -e "${INFO}: ${SCRIPT_PATH} successful"
