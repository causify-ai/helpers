# #############################################################################
# General utils
# #############################################################################

# Define strings with colors.
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
# No color.
NC='\033[0m'

INFO="${GREEN}INFO${NC}"
WARNING="${YELLOW}WARNING${NC}"
ERROR="${RED}ERROR${NC}"

#_VERB_LEVEL=2
_VERB_LEVEL=0

echo -e -n $NC


is_sourced() {
    # Function to check if the script is being sourced.
    # If the script is being sourced, $0 will not be equal to ${BASH_SOURCE[0]}
    return [[ $0 != "${BASH_SOURCE}" ]]
}


dassert_is_sourced() {
    # Ensure that this is being sourced and not executed.
    if [[ ! is_sourced ]]; then
        # We are in a script.
        echo -e "${ERROR}: This needs to be sourced and not executed"
        abort
    fi;
}


dassert_is_executed() {
    # Ensure that this is being executed and not sourced.
    if [[ is_sourced ]]; then
        # This is being executed and not sourced.
        echo -e "${ERROR}: This needs to be executed and not sourced"
        abort
    fi;
}


exit_or_return() {
    ret_value=$1
    if [[ is_sourced ]]; then
        return ret_value
    else
        exit ret_value
    fi;
}


dassert_dir_exists() {
    # Check if a directory exists.
    local dir_path="$1"
    if [[ ! -d "$dir_path" ]]; then
        echo -e "${ERROR}: Directory '$dir_path' does not exist."
        abort
    fi
}


# TODO(gp): -> dassert_file_exists
check_file_exists() {
    # Check if a filename exists.
    local file_name="$1"
    if [[ ! -f "$file_name" ]]; then
        echo -e "${ERROR}: File '$file_name' does not exist."
        abort
    fi
}


dassert_is_git_root() {
    # Check if the current directory is the root of a Git repository.
    if [[ ! -d .git ]]; then
        echo -e "${ERROR}: Current dir '$(pwd)' is not the root of a Git repo."
        abort
    fi;
}

abort() {
    if [[ -f /.dockerenv ]] ; then
        # Inside container.
        return 1
    else
        # Outside container.
        kill -INT $$
    fi
}


# TODO(gp): -> dassert_not_empty?
dassert_var_defined() {
    # Check if a variable is defined.
    # It needs to be called as `dassert_var_defined GIT_ROOT` and not
    # `dassert_var_defined "$GIT_ROOT"`.
    local var_name="$1"
    # Use indirect expansion to check the value of the variable.
    if [[ -z "${!var_name}" ]]; then
        echo -e "${ERROR}: Var '${var_name}' is not defined or is empty."
        abort
    fi;
}


dassert_eq_num_args() {
    # Check if the number of arguments passed matches expected count.
    local actual_args=$1
    local expected_args=$2
    local func_name=$3
    if [[ $actual_args -ne $expected_args ]]; then
        echo -e "${ERROR}: Function '$func_name' requires exactly $expected_args arguments, but got $actual_args"
        abort
    fi
}


dtrace() {
    # Print a debug message if _VERB_LEVEL > 1.
    dassert_eq_num_args $# 1 "dtrace"
    local msg="$1"
    if [[ "${_VERB_LEVEL:-0}" -gt 1 ]]; then
        echo -e "$msg"
    fi
}


remove_dups() {
    # Remove duplicates.
    local vars="$1"
    echo $vars | perl -e 'print join(":", grep { not $seen{$_}++ } split(/:/, scalar <>))'
}


echo_on_different_lines() {
    # Print $PATH on different lines.
    local vars="$1"
    echo $vars | perl -e 'print join("\n", grep { not $seen{$_}++ } split(/:/, scalar <>))'
}


print_python_ver() {
    echo "which python="$(which python 2>&1)
    echo "python -v="$(python --version 2>&1)
    echo "which python3="$(which python3)
    echo "python3 -v="$(python3 --version)
}


print_env_signature() {
    echo "# PATH="
    echo_on_different_lines $PATH
    #
    echo "# PYTHONPATH="
    echo_on_different_lines $PYTHONPATH
    #
    echo "# printenv="
    printenv
    #
    echo "# alias="
    alias
}


# #############################################################################
# Host utils.
# #############################################################################


print_pip_package_ver() {
    # Print package versions.
    INVOKE_VER=$(invoke --version)
    echo "# invoke=${INVOKE_VER}"
    POETRY_VER=$(poetry --version)
    echo "# poetry=${POETRY_VER}"
    DOCKER_COMPOSE_VER=$(docker-compose --version)
    echo "# docker-compose=${DOCKER_COMPOSE_VER}"
    DOCKER_VER=$(docker --version)
    echo "# docker=${DOCKER_VER}"
}


activate_venv() {
    # Activate the virtual env under `$HOME/src/venv/client_venv.${venv_tag}`.
    echo "# activate_venv()"
    local venv_tag=$1
    # Resolve the dir containing the Git client.
    # For now let's keep using the central version of /venv independenly of where
    # the Git client is (e.g., `.../src` vs `.../src_vc`).
    src_dir="$HOME/src"
    echo "src_dir=$src_dir"
    dassert_dir_exists $src_dir
    #
    venv_dir="$src_dir/venv/client_venv.${venv_tag}"
    echo "venv_dir=$venv_dir"
    dassert_dir_exists $venv_dir
    if [[ ! -d $venv_dir ]]; then
        echo -e "${WARNING}: Can't find venv_dir='$venv_dir': checking the container one"
        # The venv in the container is in a different spot. Check that.
        venv_dir="/venv/client_venv.${venv_tag}"
        if [[ ! -d $venv_dir ]]; then
            echo -e "${ERROR}: Can't find venv_dir='$venv_dir'. Create it with build.py"
            abort
        fi;
    fi;
    ACTIVATE_SCRIPT="$venv_dir/bin/activate"
    echo "# Activate virtual env '$ACTIVATE_SCRIPT'"
    check_file_exists $ACTIVATE_SCRIPT
    source $ACTIVATE_SCRIPT
    #
    print_python_ver
}


set_csfy_env_vars() {
    echo "# set_csfy_env_vars()"
    #
    export CSFY_HOST_NAME=$(hostname)
    echo "CSFY_HOST_NAME=$CSFY_HOST_NAME"
    #
    export CSFY_HOST_OS_NAME=$(uname)
    echo "CSFY_HOST_OS_NAME=$CSFY_HOST_OS_NAME"
    #
    export CSFY_HOST_USER_NAME=$(whoami)
    echo "CSFY_HOST_USER_NAME=$CSFY_HOST_USER_NAME"
    #
    export CSFY_HOST_OS_VERSION=$(uname -r)
    echo "CSFY_HOST_OS_VERSION=$CSFY_HOST_OS_VERSION"
}


set_path() {
    # Process interface.
    dassert_eq_num_args $# 1 "set_path"
    local dev_script_dir=$1
    #
    dassert_dir_exists $dev_script_dir
    dtrace "dev_script_dir=$dev_script_dir"
    # TODO(gp): Unify this as part of CmTask12257.
    if [[ -n "$GIT_ROOT_DIR" ]]; then
        # `GIT_ROOT_DIR` is available outside the container.
        GIT_ROOT=$GIT_ROOT_DIR
    elif [[ -n "$CSFY_GIT_ROOT_PATH" ]]; then
        # `CSFY_GIT_ROOT_PATH` is available inside the container.
        GIT_ROOT=$CSFY_GIT_ROOT_PATH
    fi
    export PATH=$(pwd):$PATH
    dtrace "GIT_ROOT=$GIT_ROOT"
    dassert_var_defined "GIT_ROOT"
    export PATH=$GIT_ROOT_DIR:$PATH
    # Avoid ./.mypy_cache/3.12/app/dev_scripts_helpers
    DEV_SCRIPT_HELPER_DIR=$(find ${GIT_ROOT} -name dev_scripts_helpers -type d -not -path "*.mypy_cache*")
    echo "DEV_SCRIPT_HELPER_DIR=$DEV_SCRIPT_HELPER_DIR"
    dassert_dir_exists $DEV_SCRIPT_HELPER_DIR
    dtrace "DEV_SCRIPT_HELPER_DIR=$DEV_SCRIPT_HELPER_DIR"
    # Add to the PATH all the first level directory under `dev_scripts`.
    export PATH_TMP="$(find $DEV_SCRIPT_HELPER_DIR -maxdepth 1 -type d -not -path "$(pwd)" | tr '\n' ':' | sed 's/:$//')"
    dtrace "PATH_TMP=$PATH_TMP"
    export PATH=$PATH_TMP:$PATH
    # Remove duplicates.
    export PATH=$(remove_dups $PATH)
    # Print.
    echo "PATH=$PATH"
}


set_pythonpath() {
    local helpers_root_dir="$1"
    echo "# set_pythonpath()"
    # Check if the helpers root directory is provided.
    if [[ -n "$helpers_root_dir" ]]; then
        # If provided, recursively add the helpers root directory and its
        # parents to PYTHONPATH.
        # For example, if the helpers root directory is `/data/dummy/src/orange2/amp/helpers_root`,
        # the PYTHONPATH will be set to:
        # /data/dummy/src/orange2:/data/dummy/src/orange2/amp:/data/dummy/src/orange2/amp/helpers_root
        dassert_dir_exists $helpers_root_dir
        git_root_dir=$(git rev-parse --show-toplevel)
        helpers_root_abs_path=$(realpath "$helpers_root_dir")
        # Start with the helpers root directory.
        current_path="$helpers_root_abs_path"
        while true; do
            echo "Adding $current_path to PYTHONPATH"
            # Give priority to higher level directories.
            export PYTHONPATH="$current_path:$PYTHONPATH"
            # Break if we've reached the project root.
            if [[ $current_path == $git_root_dir ]]; then
                break
            fi
            # Break if we've reached the filesystem root.
            if [[ $current_path == "/" ]]; then
                break
            fi
            # Move up one directory.
            current_path=$(dirname "$current_path")
        done
    else
        # If not, just add the current directory.
        export PYTHONPATH=$(pwd):$PYTHONPATH
    fi
    # Remove duplicates.
    export PYTHONPATH=$(remove_dups $PYTHONPATH)
    # Print.
    echo "PYTHONPATH=$PYTHONPATH"
}


is_dev_csfy() {
    # Check if we are running on the dev servers.
    # Get the host name.
    host_name=$(uname -n)
    host_names=("dev1" "dev2" "dev3")
    # Get the host name from the environment variable.
    csfy_host_name="${CSFY_HOST_NAME:-}"
    echo "host_name=$host_name csfy_host_name=$csfy_host_name"
    if [[ " ${host_names[@]} " =~ " $host_name " ]] || [[ " ${host_names[@]} " =~ " $csfy_host_name " ]]; then
        # Returns true, running the setup from dev servers.
        return 0
    else
        # Running the setup from local machine.
        return 1
    fi
}


configure_specific_project() {
    echo "# configure_specific_project()"
    # AWS profiles which are propagated to Docker.
    export CSFY_AWS_PROFILE="ck"

    # These variables are propagated to Docker.
    if is_dev_csfy; then
        # Private ECR registry base path.
        export CSFY_ECR_BASE_PATH="623860924167.dkr.ecr.eu-north-1.amazonaws.com"
    else
        # Public dockerhub registry base path.
        export CSFY_ECR_BASE_PATH="causify"
    fi

    export CSFY_AWS_S3_BUCKET="cryptokaizen-data"

    export DEV1="172.30.2.136"
    export DEV2="172.30.2.128"

    # Print some specific env vars.
    printenv | egrep "AM_|CK_|AWS_|CSFY_" | sort

    # Set up custom path to the alembic.ini file.
    # See https://alembic.sqlalchemy.org/en/latest/tutorial.html#editing-the-ini-file
    export ALEMBIC_CONFIG="alembic/alembic.ini"
}


# #############################################################################
# Docker utils.
# #############################################################################


activate_docker_venv() {
    echo "# activate_docker_venv()"
    SOURCE_PATH="/${ENV_NAME}/bin/activate"
    check_file_exists $SOURCE_PATH
    source $SOURCE_PATH
}


set_up_docker_in_docker() {
    echo "# set_up_docker_in_docker()"
    if [[ ! -d /etc/docker ]]; then
        sudo mkdir /etc/docker
    fi;
    # This is needed to run the database in dind mode (see CmTask309).
    # TODO(gp): For some reason appending to file directly `>>` doesn't work.
    sudo echo '{ "storage-driver": "vfs" }' | sudo tee -a /etc/docker/daemon.json
    # Start Docker Engine.
    # TODO(Vlad): Fix ulimit error: https://github.com/docker/cli/issues/4807.
    # Need to remove after the issue is fixed.
    sudo sed -i 's/ulimit -Hn/# ulimit -Hn/g' /etc/init.d/docker
    sudo /etc/init.d/docker start
    sudo /etc/init.d/docker status
    # Wait for Docker Engine to be started, otherwise `docker.sock` file is
    # not created so fast. This is needed to change `docker.sock` permissions.
    DOCKER_SOCK_FILE=/var/run/docker.sock
    COUNTER=0
    # Set sleep interval.
    SLEEP_SEC=0.1
    # Which is 10 seconds, i.e. `100 = 10 seconds (limit) / 0.1 seconds (sleep)`.
    COUNTER_LIMIT=100
    while true; do
        if [ -e "$DOCKER_SOCK_FILE" ]; then
            # Change permissions for Docker socket. See more on S/O:
            # `https://stackoverflow.com/questions/48957195`.
            # We do it after the Docker engine is started because `docker.sock` is
            # created only after the engine start.
            # TODO(Grisha): give permissions to the `docker` group only and not to
            # everyone, i.e. `666`.
            sudo chmod 666 $DOCKER_SOCK_FILE
            echo "Permissions for "$DOCKER_SOCK_FILE" have been changed."
            break
        elif [[ "$COUNTER" -gt "$COUNTER_LIMIT" ]]; then
            echo "Timeout limit is reached, exit script."
            exit 1
        else
            COUNTER=$((counter+1))
            sleep $SLEEP_SEC
            echo "Waiting for $DOCKER_SOCK_FILE to be created."
        fi
    done
}


set_up_docker_git() {
    echo "# set_up_docker_git()"
    VAL=$(git --version)
    echo "git --version: $VAL"
    # TODO(gp): Check https://github.com/alphamatic/amp/issues/2200#issuecomment-1101756708
    git config --global --add safe.directory /app
    if [[ -d /app/amp ]]; then
        git config --global --add safe.directory /app/amp
    fi;
    if [[ -d /src/amp ]]; then
        git config --global --add safe.directory /src/amp
    fi;
    git config --global --add safe.directory /src
    git rev-parse --show-toplevel
}


set_up_docker_aws() {
    echo "# set_up_docker_aws()"
    if [[ $AM_AWS_ACCESS_KEY_ID == "" ]]; then
        unset AM_AWS_ACCESS_KEY_ID
    else
        echo "AM_AWS_ACCESS_KEY_ID='$AM_AWS_ACCESS_KEY_ID'"
    fi;
    if [[ $AM_AWS_SECRET_ACCESS_KEY == "" ]]; then
        unset AM_AWS_SECRET_ACCESS_KEY
    else
        echo "AM_AWS_SECRET_ACCESS_KEY='***'"
    fi;
    if [[ $AM_AWS_DEFAULT_REGION == "" ]]; then
        unset AM_AWS_DEFAULT_REGION
    else
        echo "AM_AWS_DEFAULT_REGION='$AM_AWS_DEFAULT_REGION'"
    fi;
    aws configure --profile am list || true
}

# #############################################################################
# Symlink utils.
# #############################################################################

set_symlink_permissions() {
    # Remove write permissions for symlinked files to prevent accidental
    # modifications before starting to develop.
    echo "# set_symlink_permissions()"
    local directory="$1"

    # Check if the given directory is valid.
    if [ ! -d "$directory" ]; then
        echo -e "${ERROR}: '$directory' is not a valid directory."
        return 1
    fi

    # Find all symlinks in the directory and remove write permissions.
    find "$directory" -type l | while read -r symlink; do
        if [ -e "$symlink" ]; then
            chmod a-w "$symlink"
            echo -e "${INFO}:Remove write permissions for: '$symlink'"
        else
            echo -e "${WARNING}: Skipping broken symlink: '$symlink'"
        fi
    done

    return 0
}

# #############################################################################
# Parse yaml utils.
# #############################################################################

function parse_yaml {
    # Parse YAML file and outputs variable assignments in bash format.
    #
    # This function converts YAML files into bash variable declarations.
    # It handles nested structures by concatenating parent keys with underscores.
    #
    # :param $1: Path to YAML file
    # :param $2: Optional prefix for variable names
    # :return: Bash variable declarations (VAR="value") printed to stdout
    #
    # Usage:
    #   parse_yaml config.yaml [prefix]
    #
    # Example:
    #   Given YAML file with content:
    #   repo_info:
    #       repo_name: cmamp
    #       github_repo_account: causify-ai
    #
    #   Calling: parse_yaml config.yaml "REPO_CONFIG_"
    #   Outputs: REPO_CONFIG_repo_info_repo_name="cmamp"
    #            REPO_CONFIG_repo_info_github_repo_account="causify-ai"
    #
    # See https://stackoverflow.com/questions/5014632/how-can-i-parse-a-yaml-file-from-a-linux-shell-script
    local prefix=$2
    local s='[[:space:]]*' w='[a-zA-Z0-9_]*' fs=$(echo @|tr @ '\034')
    # Extract key-value pairs from YAML.
    sed -ne "s|^\($s\)\($w\)$s:$s\"\(.*\)\"$s\$|\1$fs\2$fs\3|p" \
        -e "s|^\($s\)\($w\)$s:$s'\(.*\)'$s\$|\1$fs\2$fs\3|p" \
        -e "s|^\($s\)\($w\)$s:$s\(.*\)$s\$|\1$fs\2$fs\3|p" \
        -e "s|^\($s\):|\1|" $1 |
    # Transform indented YAML hierarchical structures into flattened bash
    # variable assignments.
    awk -F$fs '{
            indent = length($1)/2;
            vname[indent] = $2;
            for (i in vname) {if (i > indent) {delete vname[i]}}
            if (length($3) > 0) {
                vn=""; for (i=0; i<indent; i++) {vn=(vn)(vname[i])("_")}
                printf("%s%s%s=\"%s\"\n", "'$prefix'",vn, $2, $3);
        }
    }'
}
