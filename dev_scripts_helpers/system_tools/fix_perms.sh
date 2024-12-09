#!/bin/bash -e

echo "CSFY_GIT_ROOT_PATH=$CSFY_GIT_ROOT_PATH"

if [[ ! -d $CSFY_GIT_ROOT_PATH ]]; then
    echo "ERROR: Can't find the root dir $CSFY_GIT_ROOT_PATH"
    exit -1
fi;

sudo chown -R $(whoami):$(whoami) $CSFY_GIT_ROOT_PATH
