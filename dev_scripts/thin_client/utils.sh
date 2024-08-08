# Define strings with colors.
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
# No color.
NC='\033[0m'

INFO="${GREEN}INFO${NC}"
WARNING="${YELLOW}WARNING${NC}"
ERROR="${RED}ERROR${NC}"

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
        exit -1
    fi;
}


dassert_is_executed() {
    # Ensure that this is being executed and not sourced.
    if [[ is_sourced ]]; then
        # This is being executed and not sourced.
        echo -e "${ERROR}: This needs to be executed and not sourced"
        return -1
    fi;
}


exit_or_return() {
    ret_value=$1
    if [[ is_sourced ]]; then
        return -1
    else
        exit -1
    fi;
}


dassert_dir_exists() {
    # Check if a directory exists.
    local dir_path="$1"
    if [[ ! -d "$dir_path" ]]; then
        echo -e "${ERROR}: Directory '$dir_path' does not exist."
        exit_or_return -1
    fi
}


# TODO(gp): -> dassert_file_exists
check_file_exists() {
    # Check if a filename exists.
    local file_name="$1"
    if [[ ! -f "$file_name" ]]; then
        echo -e "${ERROR}: File '$file_name' does not exist."
        if [[ is_sourced ]]; then
            return -1
        else
            exit -1
        fi;
    fi
}


dassert_is_git_root() {
    # Check if the current directory is the root of a Git repository.
    if [[ ! -d .git ]]; then
        echo -e "${ERROR}: Current dir '$(pwd)' is not the root of a Git repo."
        exit_or_return -1
    fi;
}


dassert_var_defined() {
    local var_name="$1"
    if [[ -n $var_name ]]; then
        echo -e "${ERROR}: Var '${var_name}' is not defined and non-empty."
        exit_or_return -1
    fi;
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
    local venv_tag=$1
    # Resolve the dir containing the Git client.
    # For now let's keep using the central version of /venv independenly of where
    # the Git client is (e.g., `.../src` vs `.../src_vc`).
    SRC_DIR="$HOME/src"
    echo "SRC_DIR=$SRC_DIR"
    dassert_dir_exists $SRC_DIR

    VENV_DIR="$SRC_DIR/venv/client_venv.${venv_tag}"
    echo "VENV_DIR=$VENV_DIR"

    if [[ ! -d $VENV_DIR ]]; then
        echo -e "${WARNING}: Can't find VENV_DIR='$VENV_DIR': checking the container one"
        # The venv in the container is in a different spot. Check that.
        VENV_DIR="/venv/client_venv.${venv_tag}"
        if [[ ! -d $VENV_DIR ]]; then
            echo -e "${ERROR}: Can't find VENV_DIR='$VENV_DIR'. Create it with build.py"
            return 1
        fi;
    fi;
    
    ACTIVATE_SCRIPT="$VENV_DIR/bin/activate"
    echo "# Activate virtual env '$ACTIVATE_SCRIPT'"
    check_file_exists $ACTIVATE_SCRIPT
    source $ACTIVATE_SCRIPT

    print_python_ver
}


set_path() {
    local dev_script_dir=$1
    echo "# Set PATH"
    export PATH=$(pwd):$PATH
    export PATH=$GIT_ROOT_DIR:$PATH
    # Add to the PATH all the first level directory under `dev_scripts`.
    export PATH="$(find $dev_script_dir -maxdepth 1 -type d -not -path "$(pwd)" | tr '\n' ':' | sed 's/:$//'):$PATH"
    # Remove duplicates.
    export PATH=$(remove_dups $PATH)
    # Print.
    echo "PATH=$PATH"
}


set_pythonpath() {
    echo "# Set PYTHONPATH"
    export PYTHONPATH=$(pwd):$PYTHONPATH
    # Remove duplicates.
    export PYTHONPATH=$(remove_dups $PYTHONPATH)
    # Print.
    echo "PYTHONPATH=$PYTHONPATH"
}


configure_specific_project() {
    # AWS profiles which are propagated to Docker.
    export CK_AWS_PROFILE="ck"

    # These variables are propagated to Docker.
    export CK_ECR_BASE_PATH="623860924167.dkr.ecr.eu-north-1.amazonaws.com"
    export CK_AWS_S3_BUCKET="cryptokaizen-data"

    export DEV1="172.30.2.136"
    export DEV2="172.30.2.128"

    # Print some specific env vars.
    printenv | egrep "AM_|CK|AWS_" | sort

    # Set up custom path to the alembic.ini file.
    # See https://alembic.sqlalchemy.org/en/latest/tutorial.html#editing-the-ini-file
    export ALEMBIC_CONFIG="alembic/alembic.ini"

    alias i="invoke"
    alias it="invoke traceback"
    alias itpb="pbpaste | traceback_to_cfile.py -i - -o cfile"
    alias ih="invoke --help"
    alias il="invoke --list"

    # Add autocomplete for `invoke`.
    #source $AMP/dev_scripts/invoke_completion.sh
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
