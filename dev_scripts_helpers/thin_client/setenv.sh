#
# Configure the local (thin) client built with `thin_client.../build.py`.
#
# NOTE: This file needs to be sourced and not executed. For this reason doesn't
# use bash and doesn't have +x permissions.
#

# - Source `utils.sh`.
# NOTE: we can't use $0 to find the path since we are sourcing this file.
GIT_ROOT_DIR=$(git rev-parse --show-toplevel)
echo "GIT_ROOT_DIR=$GIT_ROOT_DIR"

# Load thin client utils.
SOURCE_PATH=$(find $GIT_ROOT_DIR -name "thin_client_utils.sh" -type f 2>/dev/null | head -1)
# Check if file was found.
if [ -n "$SOURCE_PATH" ]; then
    echo "Thin client utils found at: $SOURCE_PATH"
else
    echo -e "ERROR: File 'thin_client_utils.sh' not found in current directory" >&2
    kill -INT $$
fi;
source $SOURCE_PATH

# Parse repo config.
echo "##> Parsing repo config"
echo $(pwd)
eval $(parse_yaml repo_config.yaml "REPO_CONF_")
for var in $(compgen -v | grep "^REPO_CONF_"); do
  echo "$var=${!var}"
done;

# NOTE: We can't use $0 to find out in which file we are in, since this file is
# sourced and not executed.
SCRIPT_PATH="dev_scripts_${REPO_CONF_runnable_dir_info_dir_suffix}/thin_client/setenv.sh"
echo "##> $SCRIPT_PATH"

if [[ $REPO_CONF_runnable_dir_info_use_helpers_as_nested_module == 1 ]]; then
    # We can reuse the thin environment of `helpers` or create a new one.
    VENV_TAG=$REPO_CONF_runnable_dir_info_venv_tag
else
    VENV_TAG="helpers"
fi;

# Give permissions to read / write to user and group.
umask 002

if [[ $REPO_CONF_runnable_dir_info_use_helpers_as_nested_module == 1 ]]; then
    # For super-repos `GIT_ROOT_DIR` points to the super-repo.
    HELPERS_ROOT_DIR="${GIT_ROOT_DIR}/helpers_root"
else
    HELPERS_ROOT_DIR="${GIT_ROOT_DIR}"
fi;

# - Activate environment
activate_venv $VENV_TAG

if [[ $REPO_CONF_runnable_dir_info_use_helpers_as_nested_module == 1 ]]; then
    HELPERS_ROOT_DIR="${GIT_ROOT_DIR}/helpers_root"
    echo "HELPERS_ROOT_DIR=$HELPERS_ROOT_DIR"
    dassert_dir_exists $HELPERS_ROOT_DIR
fi;

# - PATH

# Set vars for this dir.
CURR_DIR=$(pwd)
DEV_SCRIPT_DIR="${CURR_DIR}/dev_scripts_${REPO_CONF_runnable_dir_info_dir_suffix}"
echo "DEV_SCRIPT_DIR=$DEV_SCRIPT_DIR"
dassert_dir_exists $DEV_SCRIPT_DIR

# Set basic vars.
set_path $DEV_SCRIPT_DIR

if [[ $REPO_CONF_runnable_dir_info_use_helpers_as_nested_module == 1 ]]; then
    # Set vars for helpers_root.
    set_path "${HELPERS_ROOT_DIR}/dev_scripts_helpers"
fi;

# - PYTHONPATH
set_pythonpath

if [[ $REPO_CONF_runnable_dir_info_use_helpers_as_nested_module == 1 ]]; then
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

# Remove write permissions for symlinked files to prevent accidental
# modifications before starting to develop.
set_symlink_permissions .

# - Set specific configuration of the project.
configure_specific_project

print_env_signature

echo -e "${INFO}: ${SCRIPT_PATH} successful"
