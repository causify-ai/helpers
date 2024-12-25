#!/usr/bin/env bash

set -e

echo "CSFY_IS_SUPER_REPO=$CSFY_IS_SUPER_REPO"

FILE_NAME="devops/docker_run/entrypoint.sh"
echo "##> $FILE_NAME"

echo "UID="$(id -u)
echo "GID="$(id -g)

# - Source `utils.sh`.
# NOTE: we can't use $0 to find the path since we are sourcing this file.
echo "CSFY_GIT_ROOT_PATH=$CSFY_GIT_ROOT_PATH"
echo "CSFY_HELPERS_ROOT_PATH=$CSFY_HELPERS_ROOT_PATH"

SOURCE_PATH="${CSFY_HELPERS_ROOT_PATH}/dev_scripts_helpers/thin_client/thin_client_utils.sh"
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

# Configure Docker.
# Enable dind unless the user specifies otherwise (needed for prod image).
if [[ -z "$CSFY_ENABLE_DIND" ]]; then
    CSFY_ENABLE_DIND=1
    echo "CSFY_ENABLE_DIND=$CSFY_ENABLE_DIND"
fi;

if [[ $CSFY_ENABLE_DIND == 1 ]]; then
    set_up_docker_in_docker
fi;

DOCKER_DIR="/var/run/docker.sock"
if [[ -e $DOCKER_DIR  ]]; then
    # Give permissions to run docker without sudo.
    echo "Setting sudo docker permissions"
    ls -l $DOCKER_DIR
    sudo chmod a+rw /var/run/docker.sock
    ls -l $DOCKER_DIR
else
    echo "WARNING: $DOCKER_DIR doesn't exist"
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
    if [[ $CSFY_ENABLE_DIND == 1 ]]; then
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

invoke print_env

echo "PATH=$PATH"
echo "PYTHONPATH=$PYTHONPATH"

echo "entrypoint.sh: '$@'"
eval "$@"
