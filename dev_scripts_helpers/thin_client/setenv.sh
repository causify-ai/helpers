#
# Configure the local (thin) client built with `thin_client.../build.py`.
#
# NOTE: This file needs to be sourced and not executed. For this reason doesn't
# use bash and doesn't have +x permissions.
#

# Print the script path.
SCRIPT_PATH=$(realpath "${BASH_SOURCE[0]:-$0}")
echo "##> $SCRIPT_PATH"

GIT_ROOT_DIR=$(git rev-parse --show-toplevel)
echo "GIT_ROOT_DIR=$GIT_ROOT_DIR"

# #############################################################################
# Thin client utils.
# #############################################################################

SOURCE_PATH=$(find $GIT_ROOT_DIR -name "thin_client_utils.sh" -type f 2>/dev/null | head -1)
# Check if file was found.
if [ -n "$SOURCE_PATH" ]; then
    echo "Thin client utils found at: $SOURCE_PATH"
else
    echo -e "ERROR: File 'thin_client_utils.sh' not found in current directory" >&2
    kill -INT $$
fi;
source $SOURCE_PATH

# #############################################################################
# Repo config.
# #############################################################################

echo "##> Parsing repo config"
echo $(pwd)
eval $(parse_yaml repo_config.yaml "REPO_CONF_")
for var in $(compgen -v | grep "^REPO_CONF_"); do
  eval "echo \"$var=\$$var\""
done;

# #############################################################################
# Thin environment.
# #############################################################################

if [[ $REPO_CONF_runnable_dir_info_use_helpers_as_nested_module == 1 ]]; then
    # We can reuse the thin environment of `helpers` or create a new one.
    VENV_TAG=$REPO_CONF_runnable_dir_info_venv_tag
else
    VENV_TAG="helpers"
fi;

# - Activate environment
activate_venv $VENV_TAG

# #############################################################################
# helpers_root path.
# #############################################################################

if [[ $REPO_CONF_runnable_dir_info_use_helpers_as_nested_module == 1 ]]; then
    HELPERS_ROOT_DIR=$(find ${GIT_ROOT_DIR} \( -path '*/.git' -o -path '*/.mypy_cache' \) -prune -o -name "helpers_root" -print | head -n 1)
else
    HELPERS_ROOT_DIR="${GIT_ROOT_DIR}"
fi;

echo "HELPERS_ROOT_DIR=$HELPERS_ROOT_DIR"
dassert_dir_exists $HELPERS_ROOT_DIR

if [[ $REPO_CONF_runnable_dir_info_use_helpers_as_nested_module == 1 ]]; then
    # Set vars for helpers_root.
    set_path "${HELPERS_ROOT_DIR}/dev_scripts_helpers"
fi;

# #############################################################################
# dev_scripts_XYZ path.
# #############################################################################

CURR_DIR=$(pwd)
DEV_SCRIPT_DIR="${CURR_DIR}/dev_scripts_${REPO_CONF_runnable_dir_info_dir_suffix}"
echo "DEV_SCRIPT_DIR=$DEV_SCRIPT_DIR"
dassert_dir_exists $DEV_SCRIPT_DIR
# Set basic vars.
set_path $DEV_SCRIPT_DIR

# #############################################################################
# PYTHONPATH.
# #############################################################################

set_pythonpath $HELPERS_ROOT_DIR

# #############################################################################
# File permission.
# #############################################################################

# Give permissions to read / write to user and group.
umask 002

# Remove write permissions for symlinked files to prevent accidental
# modifications before starting to develop.
set_symlink_permissions .

# #############################################################################
# Project configuration.
# #############################################################################

# Set CSFY environment variables.
set_csfy_env_vars

# Set specific configuration of the project.
configure_specific_project

print_env_signature

echo -e "${INFO}: ${SCRIPT_PATH} successful"
