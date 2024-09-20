#!/usr/bin/env bash

set -e

# IS_SUPER_REPO=1
IS_SUPER_REPO=0
echo "IS_SUPER_REPO=$IS_SUPER_REPO"

FILE_NAME="devops/docker_run/entrypoint.sh"
echo "##> $FILE_NAME"

echo "UID="$(id -u)
echo "GID="$(id -g)

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

# Container info.
echo "AM_CONTAINER_VERSION='$AM_CONTAINER_VERSION'"

# Configure the environment.
source devops/docker_run/docker_setenv.sh

# Allow working with files outside a container.
#umask 000

# Enable dind unless the user specifies otherwise (needed for prod image).
if [[ -z "$AM_ENABLE_DIND" ]]; then
    AM_ENABLE_DIND=1
    echo "AM_ENABLE_DIND=$AM_ENABLE_DIND"
fi;

#if [[ $AM_ENABLE_DIND == 1 ]]; then
if [[ $AM_ENABLE_DIND == "TODO(Juraj): , HelpersTask16." ]]; then
    set_up_docker_in_docker
fi;

# Mount other file systems.
# mount -a || true
# sudo change perms to /mnt/tmpfs

# Git.
set_up_docker_git

# Check set-up.
if [[ $CK_TEST_SETUP ]]; then
    set_up_docker_aws
    ./devops/docker_run/test_setup.sh

    # Test the installed packages.
    if [[ $AM_ENABLE_DIND == 1 ]]; then
        VAL=$(docker -v)
        echo "docker -v: $VAL"
        VAL=$(docker-compose -v)
        echo "docker-compose -v: $VAL"
    fi;
    VAL=$(which python)
    echo "which python: $VAL"
    VAL=$(python -V)
    echo "python -V: $VAL"
    VAL=$(python -c "import helpers; print(helpers)")
    echo "helpers: $VAL"
fi;

echo "PATH=$PATH"
echo "PYTHONPATH=$PYTHONPATH"
echo "entrypoint.sh: '$@'"

# TODO(gp): eval seems to be more general, but it creates a new executable.
eval "$@"
